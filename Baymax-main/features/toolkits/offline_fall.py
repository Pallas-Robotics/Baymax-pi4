"""Local fall check-ins. Owns no devices and makes no network requests."""
import io
import json
import os
import queue
import shutil
import subprocess
import threading
import time
import wave

import numpy as np

from . import wakeword

PROMPTS = {
    "ask": "Oh no, have you fallen? Please say: Yes, I've fallen, or: No, I'm okay.",
    "ask_offline": "Oh no, have you fallen? I cannot reach my online service right now, so I need an explicit answer. Please say: Yes, I've fallen, or: No, I'm okay.",
    "repeat": "I still need an explicit answer. Have you fallen? Please say: Yes, I've fallen, or: No, I'm okay.",
    "repeat_offline": "I still cannot reach my online service, and I have not confirmed your response. Have you fallen? Please say: Yes, I've fallen, or: No, I'm okay.",
    "confirmed_ok": "Thank you. I have recorded that you said you are okay.",
    "help_requested": "I heard that you need help. I have not contacted anyone. Please use your emergency button or phone if you can.",
    "fall_confirmed": "I heard that you have fallen. I have not contacted anyone. If you need help, please use your emergency button or phone if you can.",
    "unresolved": "I could not confirm that you are okay. I have not contacted anyone. Please use your emergency button or phone if you need help.",
}
# "ok" and "okay" sound identical; competing spellings split Vosk's confidence.
OK = {"no i'm okay", "no i am okay", "i am okay", "i'm okay", "i am fine"}
HELP = {"i need help", "help", "help me", "i am not okay", "not okay", "i am not fine"}
FALLEN = {"yes i've fallen", "yes i have fallen", "i've fallen", "i have fallen"}
VOCABULARY = sorted(OK | HELP | FALLEN | {"repeat", "say again", "yes", "no", "okay"})


def response(result):
    """Only complete, confident utterances count; unknown/negated speech cannot clear a fall."""
    words = result.get("result", [])
    if not words or any(w.get("conf", 0) < 0.85 for w in words):
        return None
    text = " ".join(w.get("word", "") for w in words)
    if text in HELP:
        return "help_requested"
    if text in FALLEN:
        return "fall_confirmed"
    if text in OK:
        return "confirmed_ok"
    return None


def recognizer():
    # Unlike the wake listener, never download at runtime: an outage must not start a fetch.
    if not wakeword.model_path().is_dir():
        raise RuntimeError("Install the Vosk model first: python features/toolkits/wakeword.py --download")
    return wakeword._vosk_recognizer(VOCABULARY)


def speech():
    """Synthesize fixed prompts locally once, without opening a speaker stream."""
    from scipy.signal import resample_poly
    executable = shutil.which("espeak-ng") or shutil.which("espeak")
    if executable is None:
        raise RuntimeError("Install espeak-ng for local fall check-in speech")
    clips = {}
    for name, text in PROMPTS.items():
        data = subprocess.run([executable, "--stdout", "-s", "145", text],
                              capture_output=True, check=True, timeout=15).stdout
        with wave.open(io.BytesIO(data)) as wav:
            if wav.getsampwidth() != 2 or wav.getnchannels() != 1:
                raise ValueError("Expected mono int16 speech")
            samples = np.frombuffer(wav.readframes(60 * wav.getframerate()), dtype="<i2")
            pcm = resample_poly(samples.astype(np.float64), 48000, wav.getframerate())
            clips[name] = np.clip(pcm, -32768, 32767).astype("<i2").tobytes()
        if not clips[name]:
            raise ValueError("Empty local speech prompt")
    return clips


class Checkin:
    """One worker, bounded mic queue, fresh recognizer per question, fixed response window."""
    def __init__(self, record, pause, recognizer_factory=recognizer, speech_factory=speech,
                 clock=time.monotonic):
        self.record, self.pause = record, pause
        self.recognizer_factory, self.speech_factory = recognizer_factory, speech_factory
        self.clock = clock
        self.lock = threading.RLock()
        self.stop_event = threading.Event()
        self.request = threading.Event()
        self.queue = queue.Queue(maxsize=50)
        self.thread = None
        self.ready = False
        self.busy = False
        self.state = "starting"
        self.outcome = None
        self.pcm = b""
        self.listen_at = None
        self.deadline = None
        self.attempts = 0
        self.last_trigger = float("-inf")
        self.generation = 0
        self.offline = True

    def start(self):
        self.thread = threading.Thread(target=self.run, name="ember-offline-fall", daemon=True)
        self.thread.start()

    def status(self):
        with self.lock:
            return {"ready": self.ready, "state": self.state, "outcome": self.outcome,
                    "active": self.busy, "attempts": self.attempts}

    def trigger(self, offline=True):
        with self.lock:
            if not self.ready:
                return False
            if self.busy or self.clock() - self.last_trigger < 30:
                return True  # Both detectors can report the same incident.
            self.last_trigger = self.clock()
            self.busy = True
            self.state = "pending"
            self.outcome = None
            self.offline = offline
            self.request.set()
            return True

    def render(self, n_bytes):
        """Called by the existing output callback; silence isolates the local conversation."""
        with self.lock:
            if not self.busy:
                return None
            chunk, self.pcm = self.pcm[:n_bytes], self.pcm[n_bytes:]
            if chunk and not self.pcm:
                # Account for one output block and the speaker's echo tail before listening.
                self.listen_at = self.clock() + n_bytes / 96000 + 0.8
                self.deadline = self.listen_at + 15
                if self.state == "speaking":
                    self.state = "listening"
                elif self.state == "finishing":
                    self.state = "settling"
            return chunk.ljust(n_bytes, b"\0")

    def feed(self, samples):
        """Echo-cleaned 48 kHz mono int16 from the one existing microphone."""
        with self.lock:
            if self.state != "listening" or self.listen_at is None or self.clock() < self.listen_at:
                return
            item = (self.generation, self.clock(), np.asarray(samples, dtype=np.int16).copy())
        try:
            self.queue.put_nowait(item)
        except queue.Full:
            pass

    def _say(self, name, finishing=False):
        self.generation += 1
        self.state = "finishing" if finishing else "speaking"
        self.pcm = self.clips[name]
        self.listen_at = None
        # A failed/disconnected speaker must not leave the check-in stuck forever.
        self.deadline = self.clock() + len(self.pcm) / 96000 + 10
        self.asr.Reset()

    def _finish(self, outcome):
        self.outcome = outcome
        self.record("Offline fall check-in: " + outcome + ". No external alert sent.")
        self._say(outcome, finishing=True)

    def _question(self, repeat=False):
        name = "repeat" if repeat else "ask"
        self._say(name + "_offline" if self.offline else name)

    def tick(self):
        """Worker-only state changes; callbacks only render audio or enqueue samples."""
        with self.lock:
            now = self.clock()
            if self.request.is_set():
                self.request.clear()
                self.pause()
                self.attempts = 1
                self._question()
                self.record("Offline fall check-in started; awaiting an explicit spoken response.")
            if self.state == "settling" and now >= self.listen_at:
                self.busy = False
                self.state = self.outcome
            elif self.busy and self.deadline is not None and now >= self.deadline:
                if self.state == "listening":
                    self.attempts += 1
                    self.outcome = "unresolved"
                    self.record("Offline fall check-in remains unresolved; repeating the question.")
                    self._question(repeat=True)
                elif self.state in ("speaking", "finishing"):
                    self.outcome = self.outcome or "unresolved"
                    self.state = "unavailable"
                    self.busy = False
                    self.pcm = b""
                    self.ready = False
                    self.record("Offline fall check-in speaker unavailable; outcome: " + self.outcome)
                else:
                    self._finish("unresolved")
        try:
            generation, captured, samples = self.queue.get(timeout=0.02)
        except queue.Empty:
            return
        with self.lock:
            if (self.state != "listening" or generation != self.generation
                    or captured < self.listen_at or self.clock() - captured > 0.5):
                return
        # Recognition must not hold the lock needed by the real-time audio callbacks.
        if not self.asr.AcceptWaveform(self.converter._to_16k(samples)):
            return
        result = json.loads(self.asr.Result())
        outcome = response(result)
        with self.lock:
            if self.stop_event.is_set() or self.state != "listening" or generation != self.generation:
                return
            if outcome:
                self._finish(outcome)
            # Unclear speech keeps the listening window open. The deadline repeats
            # the question, without treating repeated noise as an explicit answer.

    def run(self):
        try:
            self.asr = self.recognizer_factory()
            self.clips = self.speech_factory()
            self.converter = wakeword.WakeListener(lambda _: None)
            with self.lock:
                if self.stop_event.is_set():
                    return
                self.ready = True
                self.state = "idle"
            self.record("Offline fall check-in ready (English, local Vosk and speech).")
            while not self.stop_event.is_set():
                self.tick()
        except Exception as error:
            with self.lock:
                self.ready = self.busy = False
                self.state = "unavailable"
                self.outcome = "unresolved" if self.outcome is None else self.outcome
                self.pcm = b""
            self.record("Offline fall check-in unavailable: " + type(error).__name__ + ". Check Vosk/espeak-ng setup; no confirmation assumed.")

    def close(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=2)
        with self.lock:
            self.ready = self.busy = False
            self.state = "stopped"
            self.pcm = b""


def enabled():
    from features.experimental import enabled as opted_in
    return opted_in("offline_fall_checkin")


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description="Prepare/check local fall speech without opening devices")
    parser.add_argument("--prepare", action="store_true", help="Download the Vosk model once (requires internet)")
    parser.add_argument("--check", action="store_true", help="Check installed Vosk and local speech, without network")
    args = parser.parse_args(argv)
    if not args.prepare and not args.check:
        parser.error("choose --prepare or --check")
    try:
        if args.prepare:
            wakeword.download_model()
        recognizer()
        speech()
    except Exception as error:
        print("Offline fall check-in setup failed: " + str(error))
        return 1
    print("Offline fall check-in dependencies ready. Microphone, speaker and fall accuracy still require board testing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
