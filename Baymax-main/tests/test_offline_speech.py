"""OFFLINE Speech contracts with synthetic PCM; no devices, network or model downloads."""
import importlib.util
import os
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import numpy as np

from features.offline_speech.bridge import ContextTimeline, Settings, SpeechWorker
from features.offline_speech.recognition import Pipeline, Recognizer, Resampler, Segmenter, Silero, WINDOW

ROOT = Path(__file__).resolve().parents[1]


class FakeVad:
    def reset(self):
        pass

    def __call__(self, samples):
        return float(samples[0])


def packet(sequence, start, *, generation=0, value=1, rate=16000):
    return dict(sequence=sequence, generation=generation, captured_at=start, rate=rate,
                pcm=np.full(WINDOW * (rate // 16000), value, dtype="<i2").tobytes())


class SpeechSettingsTests(unittest.TestCase):
    def test_tiny_and_base_only_and_thread_budget(self):
        self.assertEqual(Settings().model, "tiny")
        self.assertEqual(Settings("base", 2).threads, 2)
        for args in (("large", 1), ("tiny", 0), ("tiny", 3)):
            with self.assertRaises(ValueError):
                Settings(*args)

    def test_disabled_import_starts_no_models_threads_or_devices(self):
        code = ("import sys,threading; import features.offline_speech as s; "
                "assert not s.worker.enabled; assert s.worker.child is None; "
                "assert 'faster_whisper' not in sys.modules; assert 'numpy' not in sys.modules; "
                "assert len(threading.enumerate())==1")
        completed = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, timeout=10)
        self.assertEqual(completed.returncode, 0, completed.stderr.decode())

    def test_missing_model_is_visible_and_does_not_spawn(self):
        worker = SpeechWorker()
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {"EMBER_OFFLINE_SPEECH": "1"}), \
                patch("features.offline_speech.bridge.ROOT", Path(folder)), \
                patch("features.offline_speech.bridge.subprocess.Popen") as popen:
            worker.start()
        popen.assert_not_called()
        self.assertEqual(worker.snapshot()["state"], "error")
        self.assertIn("prepare", worker.snapshot()["detail"])

    def test_opt_in_cpu_child_has_explicit_offline_environment(self):
        worker = SpeechWorker()
        with tempfile.TemporaryDirectory() as folder:
            model = Path(folder) / ".models/offline-speech/tiny/model.bin"
            model.parent.mkdir(parents=True)
            model.touch()
            with patch.dict(os.environ, {"EMBER_OFFLINE_SPEECH": "1"}), \
                    patch("features.offline_speech.bridge.ROOT", Path(folder)), \
                    patch("features.offline_speech.bridge.subprocess.Popen") as popen, \
                    patch("features.offline_speech.bridge.threading.Thread"), \
                    patch("features.offline_speech.bridge.atexit.register"):
                worker.start()
        env = popen.call_args.kwargs["env"]
        self.assertEqual(env["HF_HUB_OFFLINE"], "1")
        self.assertEqual(env["OMP_NUM_THREADS"], "1")
        self.assertIn("features.offline_speech.process", popen.call_args.args[0])
        self.assertEqual(worker.state, "loading")


class SpeechBridgeTests(unittest.TestCase):
    def setUp(self):
        self.worker = SpeechWorker()
        self.worker.enabled = True

    def test_audio_callback_drops_on_overload_without_waiting(self):
        for _ in range(24):
            self.assertTrue(self.worker.feed(b"\0\0" * 1024, 48000))
        started = time.monotonic()
        self.assertFalse(self.worker.feed(b"\0\0" * 1024, 48000))
        self.assertLess(time.monotonic() - started, 0.1)
        self.assertEqual(self.worker.dropped_packets, 1)

    def test_speaker_overlap_is_suppressed_and_sequence_keeps_the_gap(self):
        enhancer = SimpleNamespace(speaker_active=lambda: True)
        self.assertFalse(self.worker.feed(b"\0\0", 48000, enhancer=enhancer))
        self.assertTrue(self.worker.feed(b"\0\0", 48000))
        self.assertEqual(self.worker.pending.get_nowait()["sequence"], 2)
        self.assertEqual(self.worker.suppressed_packets, 1)

    def test_tap_requires_healthy_cleanup_and_does_not_open_devices(self):
        import features.offline_speech as speech
        with patch.object(speech, "worker", self.worker):
            speech.tap(b"\0\0", 48000, None, None)
            speech.tap(b"\0\0", 48000, None, SimpleNamespace(failed=True))
        self.assertTrue(self.worker.pending.empty())
        self.assertEqual(self.worker.suppressed_packets, 2)

    def test_bad_or_empty_pcm_is_ignored(self):
        for data, rate in ((b"x", 48000), (b"", 48000), (b"\0\0", 44100)):
            self.assertFalse(self.worker.feed(data, rate))
        self.assertTrue(self.worker.pending.empty())

    def test_capture_clock_uses_adc_age(self):
        clock = SimpleNamespace(currentTime=9.0, inputBufferAdcTime=8.98)
        with patch("features.offline_speech.bridge.time.monotonic", return_value=100.0):
            self.worker.feed(b"\0\0" * 1024, 48000, time_info=clock)
        self.assertAlmostEqual(self.worker.pending.get_nowait()["captured_at"], 99.98)

    def test_stale_and_previous_session_transcripts_are_not_published(self):
        callback = Mock()
        self.worker.on_result = callback
        now = time.monotonic()
        event = dict(kind="transcript", text="hello", started_at=now - 1, ended_at=now,
                     generation=0, model="tiny", language="en")
        self.worker.reset()
        self.worker._handle(event)
        self.worker._handle(dict(event, generation=1, ended_at=now - 31))
        callback.assert_not_called()
        self.assertEqual(self.worker.stale_results, 2)

    def test_local_results_are_bounded_and_correlated_by_capture_time(self):
        now = time.monotonic()
        self.worker.observe_vision(now - 0.1, pose_available=True, face_visible=True,
                                   fall_detected=True, fall_active=True)
        callback = Mock()
        self.worker.on_result = callback
        for _ in range(25):
            self.worker._handle(dict(kind="transcript", text="I am okay", generation=0,
                                     started_at=now - 1, ended_at=now, model="tiny", language="en"))
        self.assertEqual(len(self.worker.snapshot()["transcripts"]), 20)
        self.assertTrue(callback.call_args.args[0]["vision"]["fall_detected"])
        self.assertEqual(callback.call_args.args[0]["source"], "offline_speech")

    def test_shutdown_escalates_hung_child_without_waiting_for_decode(self):
        child = Mock()
        child.poll.return_value = None
        child.wait.side_effect = [subprocess.TimeoutExpired("speech", 2), 0]
        self.worker.child = child
        self.worker.stop()
        child.terminate.assert_called_once()
        child.kill.assert_called_once()
        self.assertFalse(self.worker.enabled)

    def test_error_is_isolated_to_speech(self):
        self.worker._handle(dict(kind="error", message="model unavailable"))
        self.assertEqual(self.worker.snapshot()["state"], "error")
        self.assertFalse(self.worker.enabled)


class TimelineTests(unittest.TestCase):
    def test_fall_during_utterance_is_retained_without_future_frame(self):
        timeline = ContextTimeline()
        timeline.add(10.1, True, True, True, False)
        timeline.add(10.9, True, False, False, False)
        timeline.add(12, False, False, False, False)
        matched = timeline.match(10, 11)
        self.assertEqual(matched["captured_at"], 10.9)
        self.assertTrue(matched["fall_detected"])

    def test_missing_stale_and_future_context_are_unknown(self):
        timeline = ContextTimeline()
        self.assertIsNone(timeline.match(1, 2))
        timeline.add(1, True, True, False, False)
        timeline.add(5, True, True, True, True)
        self.assertIsNone(timeline.match(1, 2))


class SegmentationTests(unittest.TestCase):
    def test_silence_and_short_noise_never_trigger_whisper(self):
        turns = []
        segmenter = Segmenter(FakeVad(), lambda *args: turns.append(args))
        for i in range(70):
            segmenter.push(np.full(WINDOW, 1 if i == 20 else 0, np.float32), i * 0.032)
        self.assertEqual(turns, [])

    def test_preroll_and_silence_create_one_timestamped_utterance(self):
        turns = []
        segmenter = Segmenter(FakeVad(), lambda *args: turns.append(args))
        for i in range(28):
            segmenter.push(np.full(WINDOW, 1 if 10 <= i < 15 else 0, np.float32), i * 0.032)
        self.assertEqual(len(turns), 1)
        audio, start, end = turns[0]
        self.assertAlmostEqual(start, 0.16)
        self.assertAlmostEqual(end, 0.896)
        self.assertEqual(len(audio), round((end - start) * 16000))

    def test_continuous_speech_is_bounded(self):
        turns = []
        segmenter = Segmenter(FakeVad(), lambda *args: turns.append(args))
        for i in range(400):
            segmenter.push(np.ones(WINDOW, np.float32), i * 0.032)
        self.assertEqual(len(turns), 1)
        self.assertLessEqual(len(turns[0][0]), 16000 * 12)

    def test_streaming_resampler_matches_single_block_and_removes_alias(self):
        pcm = (np.sin(np.arange(48000) * 2 * np.pi * 12000 / 48000) * 16000).astype("<i2").tobytes()
        whole = Resampler(48000).process(pcm)
        resampler = Resampler(48000)
        split = np.concatenate([resampler.process(pcm[i:i + 2048]) for i in range(0, len(pcm), 2048)])
        np.testing.assert_allclose(split, whole, atol=1e-6)
        self.assertEqual(len(split), 16000)
        self.assertLess(np.sqrt(np.mean(split[100:] ** 2)), 0.01)


class PipelineTests(unittest.TestCase):
    def recognizer(self):
        return SimpleNamespace(vad=FakeVad(), settings=Settings(), transcribe=Mock(return_value=("hello", "en")))

    def test_packet_loss_and_reconnect_discard_partial_utterance(self):
        pipeline = Pipeline(self.recognizer(), lambda event: None, clock=lambda: 0)
        self.addCleanup(pipeline.close)
        pipeline.accept(packet(1, 0))
        pipeline.segmenter.push(np.ones(WINDOW), 0)
        self.assertTrue(pipeline.segmenter.frames)
        pipeline.accept(packet(3, 0.064, value=0))
        self.assertFalse(pipeline.segmenter.frames)
        pipeline.segmenter.push(np.ones(WINDOW), 0.1)
        pipeline.accept(packet(4, 0.096, generation=1, value=0))
        self.assertFalse(pipeline.segmenter.frames)

    def test_slow_decode_does_not_stop_vad_and_pending_turn_is_bounded(self):
        entered, release = threading.Event(), threading.Event()
        recognizer = self.recognizer()
        def decode(samples):
            entered.set()
            release.wait(3)
            return "hello", "en"
        recognizer.transcribe = decode
        events = []
        pipeline = Pipeline(recognizer, events.append, clock=lambda: 0)
        pipeline.generation = 0
        self.addCleanup(pipeline.close)
        self.addCleanup(release.set)
        pipeline._utterance(np.ones(WINDOW), 0, 1)
        self.assertTrue(entered.wait(2))
        pipeline._utterance(np.ones(WINDOW), 1, 2)
        pipeline._utterance(np.ones(WINDOW), 2, 3)
        self.assertEqual(pipeline.turns.qsize(), 1)
        self.assertIn(dict(kind="dropped"), events)
        pipeline.accept(packet(1, 0, value=0))
        self.assertEqual(pipeline.offset, WINDOW)
        release.set()

    def test_native_error_is_reported(self):
        received = threading.Event()
        events = []
        recognizer = self.recognizer()
        recognizer.transcribe.side_effect = RuntimeError("native failure")
        def emit(event):
            events.append(event)
            if event["kind"] == "error":
                received.set()
        pipeline = Pipeline(recognizer, emit, clock=lambda: 0)
        pipeline.generation = 0
        self.addCleanup(pipeline.close)
        pipeline._utterance(np.ones(WINDOW), 0, 1)
        self.assertTrue(received.wait(2))
        self.assertTrue(any(e["kind"] == "error" for e in events))

    def test_recognizer_uses_only_local_cpu_int8_and_skips_hallucinated_segments(self):
        model = Mock()
        model.transcribe.return_value = ([SimpleNamespace(text="hello", no_speech_prob=0.1, avg_logprob=-0.2),
                                         SimpleNamespace(text="noise", no_speech_prob=0.9, avg_logprob=-0.2)],
                                        SimpleNamespace(language="en"))
        whisper_module = SimpleNamespace(WhisperModel=Mock(return_value=model))
        with patch.dict(sys.modules, {"faster_whisper": whisper_module}), \
                patch("features.offline_speech.recognition.Silero"):
            recognizer = Recognizer(Settings())
            text, language = recognizer.transcribe(np.zeros(WINDOW))
        options = whisper_module.WhisperModel.call_args.kwargs
        self.assertEqual(options["device"], "cpu")
        self.assertEqual(options["compute_type"], "int8")
        self.assertTrue(options["local_files_only"])
        self.assertEqual(options["cpu_threads"], 1)
        self.assertEqual((text, language), ("hello", "en"))


@unittest.skipUnless(importlib.util.find_spec("faster_whisper"), "optional speech dependencies not installed")
class NativeVadTests(unittest.TestCase):
    def test_bundled_silero_streaming_contract_on_silence(self):
        vad = Silero()
        values = [vad(np.zeros(WINDOW, dtype=np.float32)) for _ in range(40)]
        self.assertTrue(all(np.isfinite(p) and 0 <= p <= 1 for p in values))
        self.assertLess(max(values), 0.5)


if __name__ == "__main__":
    unittest.main()
