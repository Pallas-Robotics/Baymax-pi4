"""Exercise the actual v10 mic/camera hooks with the existing virtual-device harness."""
from collections import deque
import time
import unittest
from unittest.mock import patch

from features.offline_speech.bridge import SpeechWorker
import runtime_monitor as monitor
import test_v10_runtime as v10


class OfflineSpeechRuntimeTests(unittest.TestCase):
    def test_shared_mic_tap_receives_cleaned_pcm_and_existing_raw_recording_survives(self):
        case = v10.V10WaitingCueTests("test_microphone_hook_uses_cleaned_pcm_and_preserves_raw_recording")
        result = unittest.TestResult()
        with patch("features.offline_speech.tap") as tap, \
                patch("features.offline_speech.worker.reset") as reset:
            case.run(result)
        self.assertTrue(result.wasSuccessful(), result.errors + result.failures)
        tap.assert_called_once()
        self.assertEqual(tap.call_args.args[:2], (bytes(2048), 48000))
        reset.assert_called_once()

    def test_shared_camera_publishes_only_metadata_with_capture_time(self):
        harness = v10.PoseProcessRestartTests()
        before = time.monotonic()
        with patch("features.offline_speech.worker.observe_vision") as observe:
            _, frames, _, _, _ = harness.run_thread([harness.Working()])
        self.assertGreater(observe.call_count, 0)
        for call in observe.call_args_list:
            self.assertGreaterEqual(call.args[0], before)
            self.assertLessEqual(call.args[0], time.monotonic())
            self.assertEqual(set(call.kwargs), {"pose_available", "face_visible", "fall_detected", "fall_active"})
            self.assertTrue(call.kwargs["pose_available"])
        self.assertGreater(len(frames), 1)

    def test_local_monitor_results_do_not_generate_duplicate_gemini_transcripts_or_state(self):
        worker = SpeechWorker(on_result=lambda result: monitor.record("offline_speech", "Local speech: " + result["text"]))
        with patch("features.offline_speech.worker", worker), \
                patch.object(monitor, "transcripts", deque()), \
                patch.object(monitor, "events", deque()), \
                patch.object(monitor, "state", "listening"):
            now = time.monotonic()
            worker._handle(dict(kind="transcript", text="hello", generation=0, started_at=now - 1,
                                ended_at=now, model="tiny", language="en"))
            snapshot = monitor.snapshot()
        self.assertEqual(snapshot["state"], "listening")
        self.assertEqual(snapshot["transcripts"], [])
        self.assertEqual(snapshot["capabilities"]["offline_speech"]["transcripts"][0]["text"], "hello")
        self.assertEqual(snapshot["events"][0]["state"], "offline_speech")
