"""Silero endpointing and bounded Whisper decoding, used only in the speech child."""
from collections import deque
import queue
import threading
import time

import numpy as np

RATE = 16000
WINDOW = 512


class Resampler:
    """Continuous low-pass + 3:1 decimation; retain filter state and sample phase."""
    def __init__(self, rate):
        from scipy import signal
        self.rate = rate
        if rate not in (16000, 48000):
            raise ValueError("Offline speech needs mono 16/48 kHz PCM16")
        self.signal = signal
        self.taps = signal.firwin(63, 7200, fs=48000)
        self.state = np.zeros(62)
        self.phase = 0

    def process(self, pcm):
        samples = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768.0
        if self.rate == RATE:
            return samples
        filtered, self.state = self.signal.lfilter(self.taps, [1.0], samples, zi=self.state)
        result = filtered[self.phase::3].astype(np.float32)
        self.phase = (self.phase - len(samples)) % 3
        return result


class Silero:
    """Streaming state for faster-whisper 1.2.1's bundled Silero v6 ONNX model.

    Uses the upstream input/h/c contract (faster_whisper/vad.py); CPU session
    and model files are supplied by faster-whisper, without torch or downloads.
    """
    def __init__(self):
        from faster_whisper.vad import get_vad_model
        self.session = get_vad_model().session
        self.reset()

    def reset(self):
        self.h = np.zeros((1, 1, 128), dtype=np.float32)
        self.c = np.zeros((1, 1, 128), dtype=np.float32)
        self.context = np.zeros((1, 64), dtype=np.float32)

    def __call__(self, samples):
        samples = samples.reshape(1, WINDOW)
        output, self.h, self.c = self.session.run(
            None, {"input": np.concatenate((self.context, samples), axis=1), "h": self.h, "c": self.c})
        self.context = samples[:, -64:].copy()
        return float(np.asarray(output).reshape(-1)[0])


class Segmenter:
    """160 ms pre-roll, 400 ms end silence; cap each utterance at 12 seconds."""
    def __init__(self, vad, emit):
        self.vad, self.emit = vad, emit
        self.reset()

    def reset(self):
        self.vad.reset()
        self.pre = deque(maxlen=5)
        self.frames = []
        self.speech_samples = 0
        self.silent_samples = 0
        self.started_at = None

    def push(self, samples, started_at):
        probability = self.vad(samples)
        voiced = probability >= (0.35 if self.frames else 0.5)
        if not self.frames:
            if not voiced:
                self.pre.append((samples.copy(), started_at))
                return
            self.started_at = self.pre[0][1] if self.pre else started_at
            self.frames = [p[0] for p in self.pre]
            self.pre.clear()
        self.frames.append(samples.copy())
        self.speech_samples += WINDOW if voiced else 0
        self.silent_samples = 0 if voiced else self.silent_samples + WINDOW
        if self.silent_samples >= RATE * 0.4 or len(self.frames) * WINDOW >= RATE * 12:
            if self.speech_samples >= RATE * 0.16:
                self.emit(np.concatenate(self.frames), self.started_at, started_at + WINDOW / RATE)
            self.reset()


class Recognizer:
    def __init__(self, settings):
        from faster_whisper import WhisperModel
        self.settings = settings
        self.model = WhisperModel(str(settings.model_dir), device="cpu", compute_type="int8",
                                  cpu_threads=settings.threads, num_workers=1, local_files_only=True)
        self.vad = Silero()

    def transcribe(self, samples):
        segments, info = self.model.transcribe(samples, beam_size=1, best_of=1, temperature=0,
                                               language=self.settings.language, vad_filter=False,
                                               condition_on_previous_text=False)
        text = " ".join(s.text.strip() for s in segments
                        if s.no_speech_prob < 0.6 and s.avg_logprob >= -1).strip()
        return text, info.language


class Pipeline:
    def __init__(self, recognizer, emit, clock=time.monotonic):
        self.recognizer, self.emit, self.clock = recognizer, emit, clock
        self.turns = queue.Queue(maxsize=1)
        self.segmenter = Segmenter(recognizer.vad, self._utterance)
        self.sequence = None
        self.generation = None
        self.rate = None
        self.offset = 0
        self.pending = np.empty(0, dtype=np.float32)
        self.stop_event = threading.Event()
        self.decoder = threading.Thread(target=self._decode, name="whisper-cpu", daemon=True)
        self.decoder.start()

    def _utterance(self, samples, started_at, ended_at):
        try:
            self.turns.put_nowait((samples, started_at, ended_at, self.generation))
        except queue.Full:
            self.emit(dict(kind="dropped"))

    def accept(self, packet):
        seq, generation, rate = packet["sequence"], packet["generation"], packet["rate"]
        captured_at = packet["captured_at"]
        if (self.sequence is None or seq != self.sequence + 1 or generation != self.generation
                or rate != self.rate or abs(captured_at - self.expected_at) > 0.15):
            self.segmenter.reset()
            self.resampler = Resampler(rate)
            self.pending = np.empty(0, dtype=np.float32)
            self.started_at, self.offset = captured_at, 0
        self.sequence, self.generation, self.rate = seq, generation, rate
        self.expected_at = captured_at + len(packet["pcm"]) / (2 * rate)
        self.pending = np.concatenate((self.pending, self.resampler.process(packet["pcm"])))
        while len(self.pending) >= WINDOW:
            self.segmenter.push(self.pending[:WINDOW], self.started_at + self.offset / RATE)
            self.offset += WINDOW
            self.pending = self.pending[WINDOW:]

    def _decode(self):
        while not self.stop_event.is_set():
            try:
                samples, start, end, generation = self.turns.get(timeout=0.2)
            except queue.Empty:
                continue
            if self.clock() - end > 5 or generation != self.generation:
                self.emit(dict(kind="dropped"))
                continue
            self.emit(dict(kind="decoding", active=True))
            try:
                text, language = self.recognizer.transcribe(samples)
                if text:
                    self.emit(dict(kind="transcript", text=text[:4000], language=language,
                                   model=self.recognizer.settings.model, generation=generation,
                                   started_at=start, ended_at=end, duration_s=round(end - start, 3)))
            except Exception as error:
                self.emit(dict(kind="error", message=f"Whisper decoding failed: {type(error).__name__}"))
                self.stop_event.set()
            finally:
                self.emit(dict(kind="decoding", active=False))

    def close(self):
        self.stop_event.set()
        self.decoder.join(timeout=0.5)
