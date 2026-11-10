"""Nonblocking PCM tap and timestamp correlation; no model imports or devices here."""
import atexit
from collections import deque
from dataclasses import dataclass
import os
from pathlib import Path
import pickle
import queue
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    model: str = "tiny"
    threads: int = 1
    language: str | None = None

    def __post_init__(self):
        if self.model not in ("tiny", "base"):
            raise ValueError("EMBER_OFFLINE_SPEECH_MODEL must be tiny or base")
        if not 1 <= self.threads <= 2:
            raise ValueError("EMBER_OFFLINE_SPEECH_THREADS must be 1 or 2")

    @property
    def model_dir(self):
        return ROOT / ".models" / "offline-speech" / self.model

    @classmethod
    def from_env(cls):
        return cls(os.getenv("EMBER_OFFLINE_SPEECH_MODEL", "tiny"),
                   int(os.getenv("EMBER_OFFLINE_SPEECH_THREADS", "1")),
                   os.getenv("EMBER_OFFLINE_SPEECH_LANGUAGE") or None)


class ContextTimeline:
    """Keep metadata only; a delayed transcript never acquires a future camera frame."""
    def __init__(self):
        self.lock = threading.Lock()
        self.frames = deque(maxlen=600)

    def add(self, captured_at, pose_available, face_visible, fall_detected, fall_active):
        with self.lock:
            self.frames.append(dict(captured_at=captured_at, pose_available=bool(pose_available),
                                    face_visible=bool(face_visible), fall_detected=bool(fall_detected),
                                    fall_active=bool(fall_active)))

    def match(self, started_at, ended_at):
        with self.lock:
            frames = [dict(f) for f in self.frames
                      if started_at - 0.5 <= f["captured_at"] <= ended_at]
        if not frames or ended_at - frames[-1]["captured_at"] > 0.5:
            return None
        latest = frames[-1]
        latest["age_ms"] = round((ended_at - latest["captured_at"]) * 1000, 1)
        latest["fall_detected"] = any(f["fall_detected"] for f in frames)
        latest["fall_active"] = any(f["fall_active"] for f in frames)
        return latest


class SpeechWorker:
    def __init__(self, on_result=None, on_status=None):
        self.on_result = on_result
        self.on_status = on_status
        self.timeline = ContextTimeline()
        self.lock = threading.Lock()
        self.pending = queue.Queue(maxsize=24)
        self.results = deque(maxlen=20)
        self.child = None
        self.enabled = False
        self.closed = threading.Event()
        self.generation = 0
        self.sequence = 0
        self.state = "disabled"
        self.detail = "Set EMBER_OFFLINE_SPEECH=1 to opt in"
        self.settings = Settings()
        self.dropped_packets = 0
        self.suppressed_packets = 0
        self.dropped_utterances = 0
        self.stale_results = 0
        self.last_seen = 0.0
        self.last_feed = 0.0
        self.decoding_since = None

    def _status(self, state, detail):
        with self.lock:
            self.state, self.detail = state, detail
        if self.on_status:
            self.on_status(state, detail)

    def start(self):
        if self.child is not None or self.closed.is_set() or os.getenv("EMBER_OFFLINE_SPEECH", "0") != "1":
            return
        try:
            self.settings = Settings.from_env()
            if not (self.settings.model_dir / "model.bin").is_file():
                raise FileNotFoundError("Model missing; run python -m features.offline_speech.prepare --model "
                                        + self.settings.model)
            env = dict(os.environ, OMP_NUM_THREADS=str(self.settings.threads),
                       OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
                       HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
            self.child = subprocess.Popen([sys.executable, "-m", "features.offline_speech.process",
                                           "--model", self.settings.model, "--threads", str(self.settings.threads),
                                           *(["--language", self.settings.language] if self.settings.language else [])],
                                          cwd=ROOT, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            self.enabled = True
            self.last_seen = time.monotonic()
            self._status("loading", "Loading local Whisper + Silero on CPU")
            for target, name in ((self._write, "speech-input"), (self._read, "speech-results"),
                                 (self._watch, "speech-watchdog")):
                threading.Thread(target=target, name=name, daemon=True).start()
            atexit.register(self.stop)
        except Exception as error:
            self.enabled = False
            self._status("error", f"Offline speech unavailable: {error}")

    def reset(self):
        # A new microphone session must not publish a result from its predecessor.
        with self.lock:
            self.generation += 1

    def feed(self, pcm, rate, captured_at=None, *, time_info=None, enhancer=None, blocked=False):
        if not self.enabled or self.closed.is_set():
            return False
        self.sequence += 1
        if blocked or (enhancer is not None and enhancer.speaker_active()):
            self.suppressed_packets += 1
            return False
        if rate not in (16000, 48000) or not pcm or len(pcm) % 2:
            return False
        now = time.monotonic()
        if captured_at is None:
            captured_at = now - len(pcm) / (2 * rate)
            if time_info is not None:
                try:
                    age = float(time_info.currentTime - time_info.inputBufferAdcTime)
                    if 0 <= age < 1:
                        captured_at = now - age
                except (AttributeError, TypeError, ValueError):
                    pass
        self.last_feed = now
        packet = dict(pcm=bytes(pcm), rate=rate, captured_at=captured_at,
                      sequence=self.sequence, generation=self.generation)
        try:
            self.pending.put_nowait(packet)
            return True
        except queue.Full:
            self.dropped_packets += 1
            return False

    def observe_vision(self, captured_at, *, pose_available, face_visible, fall_detected, fall_active):
        if self.enabled:
            self.timeline.add(captured_at, pose_available, face_visible, fall_detected, fall_active)

    def _write(self):
        try:
            while not self.closed.is_set():
                try:
                    packet = self.pending.get(timeout=0.2)
                except queue.Empty:
                    continue
                # Old PCM is discarded rather than recognized out of context.
                if time.monotonic() - packet["captured_at"] > 1 or packet["generation"] != self.generation:
                    self.dropped_packets += 1
                    continue
                pickle.dump(packet, self.child.stdin, protocol=pickle.HIGHEST_PROTOCOL)
                self.child.stdin.flush()
        except (OSError, ValueError):
            if not self.closed.is_set():
                self._fail("Speech input process stopped")

    def _handle(self, event):
        self.last_seen = time.monotonic()
        kind = event["kind"]
        if kind == "ready":
            self._status("running", "Whisper " + self.settings.model + " + Silero VAD (CPU)")
        elif kind == "decoding":
            self.decoding_since = self.last_seen if event["active"] else None
        elif kind == "dropped":
            if event.get("scope") == "packet":
                self.dropped_packets += 1
            else:
                self.dropped_utterances += 1
        elif kind == "error":
            self._fail(event["message"])
        elif kind == "transcript":
            if event["generation"] != self.generation or self.last_seen - event["ended_at"] > 30:
                self.stale_results += 1
                return
            result = {key: value for key, value in event.items() if key != "kind"}
            result["source"] = "offline_speech"
            result["vision"] = self.timeline.match(result["started_at"], result["ended_at"])
            result["latency_ms"] = round(max(0, self.last_seen - result["ended_at"]) * 1000, 1)
            with self.lock:
                self.results.append(result)
            if self.on_result:
                self.on_result(dict(result))

    def _read(self):
        try:
            while not self.closed.is_set():
                self._handle(pickle.load(self.child.stdout))
        except (EOFError, OSError, ValueError, pickle.UnpicklingError):
            if not self.closed.is_set():
                self._fail("Speech result process stopped")

    def _watch(self):
        while not self.closed.wait(0.5):
            now = time.monotonic()
            if self.child.poll() is not None:
                self._fail("Speech process exited")
                return
            timed_out = ((self.state == "loading" and now - self.last_seen > 60)
                         or (self.state == "running" and now - self.last_feed < 2 and now - self.last_seen > 5)
                         or (self.decoding_since is not None and now - self.decoding_since > 30))
            if timed_out:
                self._fail("Speech worker timed out; restart Ember to retry")
                return

    def _fail(self, detail):
        if self.closed.is_set():
            return
        self._status("error", detail)
        self.stop(keep_error=True)

    def stop(self, keep_error=False):
        self.enabled = False
        self.closed.set()
        child = self.child
        if child is not None:
            # Never wait for a model or a blocked pipe to finish during shutdown.
            if child.poll() is None:
                child.terminate()
            try:
                child.wait(timeout=2)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=2)
            if child.stdin:
                try:
                    child.stdin.close()
                except (OSError, ValueError):
                    pass
            if child.stdout:
                child.stdout.close()
        if not keep_error and self.state != "disabled":
            self._status("stopped", "Offline speech stopped")

    def snapshot(self):
        with self.lock:
            return dict(state=self.state, detail=self.detail, author="natey", model=self.settings.model,
                        device="CPU", cpu_threads=self.settings.threads,
                        pid=self.child.pid if self.child else None,
                        dropped_packets=self.dropped_packets, suppressed_packets=self.suppressed_packets,
                        dropped_utterances=self.dropped_utterances, stale_results=self.stale_results,
                        transcripts=[dict(r) for r in self.results])
