"""Local fall check-ins with synthetic PCM; no capture, downloads or Gemini."""
import asyncio
import json
import os
import threading
import time
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import numpy as np

from features.toolkits import offline_fall as fall
from test_public_core_integration import load_function

V10 = Path(__file__).resolve().parents[1] / "realtime_gemini_10.py"


def result(text, confidence=1):
    return {"text": text, "result": [{"word": word, "conf": confidence} for word in text.split()]}


class OfflineFallTests(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.record, self.pause = Mock(), Mock()
        self.checkin = fall.Checkin(self.record, self.pause, clock=lambda: self.now)
        self.checkin.asr = Mock()
        self.checkin.clips = {key: b"\x01\x00" * 480 for key in fall.PROMPTS}
        self.checkin.converter = SimpleNamespace(_to_16k=lambda samples: samples.tobytes())
        self.checkin.ready = True

    def ask(self):
        self.assertTrue(self.checkin.trigger())
        self.checkin.tick()
        self.assertEqual(self.checkin.state, "speaking")
        self.checkin.render(960)
        self.now = self.checkin.listen_at + 0.01

    def answer(self, text, confidence=1):
        self.checkin.asr.AcceptWaveform.return_value = True
        self.checkin.asr.Result.return_value = json.dumps(result(text, confidence))
        self.checkin.feed(np.ones(480, dtype=np.int16))
        self.checkin.tick()

    def test_only_explicit_confident_final_answers_confirm(self):
        for text in ("i am okay", "i'm okay", "i am fine", "no i'm okay", "no i am okay"):
            self.assertEqual(fall.response(result(text)), "confirmed_ok")
        for text in ("yes", "okay", "i am not okay", "not okay", "i am okay [unk]", "[unk] i am okay"):
            self.assertNotEqual(fall.response(result(text)), "confirmed_ok")
        self.assertIsNone(fall.response(result("i am okay", 0.7)))
        self.assertIsNone(fall.response({"text": "i am okay"}))

    def test_yes_fallen_confirms_the_fall_not_safety(self):
        self.ask()
        self.answer("yes i've fallen")
        self.assertEqual(self.checkin.outcome, "fall_confirmed")
        self.assertFalse(self.checkin.outcome == "confirmed_ok")
        self.assertIsNone(fall.response(result("yes")))
        self.assertIsNone(fall.response(result("no")))

    def test_connected_question_does_not_claim_an_outage(self):
        self.checkin.trigger(offline=False)
        self.checkin.tick()
        self.assertEqual(self.checkin.pcm, self.checkin.clips["ask"])
        self.assertNotIn("online service", fall.PROMPTS["ask"])
        self.assertIn("online service", fall.PROMPTS["ask_offline"])

    def test_help_and_negation_never_clear_a_fall(self):
        for text in fall.HELP:
            self.assertEqual(fall.response(result(text)), "help_requested")
        self.ask()
        self.answer("i am not okay")
        self.assertEqual(self.checkin.outcome, "help_requested")
        self.assertNotIn("contacted someone", fall.PROMPTS["help_requested"])

    def test_confirmation_is_recorded_and_acknowledged_then_releases_audio(self):
        self.ask()
        self.pause.assert_called_once()
        self.answer("i am okay")
        self.assertEqual(self.checkin.outcome, "confirmed_ok")
        self.assertTrue(self.checkin.busy)
        self.checkin.render(960)
        self.now = self.checkin.listen_at + 0.01
        self.checkin.tick()
        self.assertFalse(self.checkin.busy)
        self.assertIsNone(self.checkin.render(960))
        self.assertEqual(self.checkin.status()["outcome"], "confirmed_ok")

    def test_partial_results_never_confirm(self):
        self.ask()
        self.checkin.asr.AcceptWaveform.return_value = False
        self.checkin.feed(np.ones(480, dtype=np.int16))
        self.checkin.tick()
        self.assertIsNone(self.checkin.outcome)
        self.checkin.asr.Result.assert_not_called()

    def test_audio_callbacks_continue_while_vosk_is_recognizing(self):
        import threading
        self.ask()
        samples = np.ones(480, dtype=np.int16)
        def recognize(_pcm):
            callback = threading.Thread(target=lambda: (self.checkin.render(960), self.checkin.feed(samples)))
            callback.start()
            callback.join(timeout=0.5)
            self.assertFalse(callback.is_alive(), "Vosk blocked the audio callbacks")
            return False
        self.checkin.asr.AcceptWaveform.side_effect = recognize
        self.checkin.feed(samples)
        self.checkin.tick()

    def test_self_echo_and_old_audio_are_not_answers(self):
        self.checkin.trigger()
        self.checkin.tick()
        self.checkin.feed(np.ones(480, dtype=np.int16))
        self.assertTrue(self.checkin.queue.empty())
        self.checkin.render(960)
        self.checkin.feed(np.ones(480, dtype=np.int16))
        self.assertTrue(self.checkin.queue.empty())
        self.now = self.checkin.listen_at + 1
        self.checkin.queue.put((self.checkin.generation - 1, self.now, np.ones(480)))
        self.checkin.tick()
        self.checkin.asr.AcceptWaveform.assert_not_called()
        self.checkin.queue.put((self.checkin.generation, self.now - 1, np.ones(480)))
        self.checkin.tick()
        self.checkin.asr.AcceptWaveform.assert_not_called()

    def test_silence_keeps_repeating_and_never_assumes_safety(self):
        self.ask()
        self.now = self.checkin.deadline + 1
        self.checkin.tick()
        self.assertEqual(self.checkin.attempts, 2)
        self.assertEqual(self.checkin.state, "speaking")
        self.checkin.render(960)
        self.now = self.checkin.deadline + 1
        self.checkin.tick()
        self.assertEqual(self.checkin.outcome, "unresolved")
        self.assertTrue(self.checkin.busy)
        self.assertEqual(self.checkin.attempts, 3)

    def test_ambiguous_answers_wait_for_deadline_then_repeat(self):
        self.ask()
        self.answer("okay")
        self.assertIsNone(self.checkin.outcome)
        self.answer("yes")
        self.assertIsNone(self.checkin.outcome)
        self.assertEqual(self.checkin.state, "listening")
        self.now = self.checkin.deadline + 1
        self.checkin.tick()
        self.assertEqual(self.checkin.outcome, "unresolved")
        self.assertTrue(self.checkin.busy)
        self.checkin.render(960)
        self.now = self.checkin.listen_at + 1
        self.answer("no i'm okay")
        self.assertEqual(self.checkin.outcome, "confirmed_ok")

    def test_speaker_failure_is_unresolved_and_disables_local_handler(self):
        self.ask()
        self.answer("repeat")
        self.now = self.checkin.deadline + 1
        self.checkin.tick()
        self.now = self.checkin.deadline + 1
        self.checkin.tick()
        self.assertEqual(self.checkin.outcome, "unresolved")
        self.assertFalse(self.checkin.ready)
        self.assertFalse(self.checkin.busy)

    def test_duplicate_detector_events_do_not_restart_the_question(self):
        self.ask()
        self.assertTrue(self.checkin.trigger())
        self.assertFalse(self.checkin.request.is_set())
        self.assertEqual(self.checkin.attempts, 1)

    def test_no_model_means_no_download_and_no_assumed_confirmation(self):
        with patch.object(fall.wakeword, "model_path", return_value=Path("/missing-vosk-model")), \
                patch.object(fall.wakeword, "_vosk_recognizer") as factory:
            with self.assertRaises(RuntimeError):
                fall.recognizer()
        factory.assert_not_called()
        self.checkin.recognizer_factory = Mock(side_effect=RuntimeError("missing"))
        self.checkin.run()
        self.assertEqual(self.checkin.state, "unavailable")
        self.assertFalse(self.checkin.trigger())

    def test_no_speech_engine_is_an_explicit_setup_failure(self):
        with patch.object(fall.shutil, "which", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "espeak-ng"):
                fall.speech()

    def test_setup_check_never_downloads_or_opens_devices(self):
        with patch.object(fall, "recognizer") as asr, patch.object(fall, "speech") as speech, \
                patch.object(fall.wakeword, "download_model") as download:
            self.assertEqual(fall.main(["--check"]), 0)
        asr.assert_called_once()
        speech.assert_called_once()
        download.assert_not_called()

    def test_setup_prepare_downloads_explicitly_and_reports_failures(self):
        with patch.object(fall, "recognizer"), patch.object(fall, "speech"), \
                patch.object(fall.wakeword, "download_model") as download:
            self.assertEqual(fall.main(["--prepare"]), 0)
        download.assert_called_once()
        with patch.object(fall, "recognizer", side_effect=RuntimeError("missing model")):
            self.assertEqual(fall.main(["--check"]), 1)

    def test_bounded_feed_and_close(self):
        self.ask()
        for _ in range(100):
            self.checkin.feed(np.ones(480, dtype=np.int16))
        self.assertEqual(self.checkin.queue.qsize(), 50)
        self.checkin.close()
        self.assertFalse(self.checkin.ready)
        self.assertFalse(self.checkin.busy)


class RuntimeIntegrationTests(unittest.TestCase):
    def load(self, name, ns):
        with patch("test_public_core_integration.CORE", V10):
            return load_function(name, ns)

    def test_outage_audio_and_checkin_answers_are_not_queued_for_upload(self):
        ns = {"_gemini_connected": False, "_offline_fall": None, "audio_queue_mic": asyncio.Queue(maxsize=2)}
        enqueue = self.load("_queue_microphone", ns)
        enqueue("offline")
        self.assertTrue(ns["audio_queue_mic"].empty())
        ns["_gemini_connected"] = True
        ns["_offline_fall"] = SimpleNamespace(busy=True)
        enqueue("local answer")
        self.assertTrue(ns["audio_queue_mic"].empty())
        ns["_offline_fall"].busy = False
        for message in (1, 2, 3):
            enqueue(message)
        self.assertEqual([ns["audio_queue_mic"].get_nowait() for _ in range(2)], [2, 3])

    def test_local_answer_reaches_vosk_without_scheduling_a_cloud_upload(self):
        import queue
        import time
        local = Mock(busy=True)
        upload = Mock()
        samples = np.ones((480, 1), dtype=np.int16)
        class Stream:
            def __init__(self, **kwargs):
                self.callback = kwargs["callback"]
            def __enter__(self):
                self.callback(samples, 480, None, None)
            def __exit__(self, *args):
                pass
        ns = {"asyncio": asyncio, "np": np, "queue": queue, "time": time,
              "_audio_enhancer": None, "_offline_fall": local, "_waiting_cue": None,
              "_audio_record_queue": queue.Queue(), "INPUT_CHANNELS": 1,
              "INTERRUPT_RMS_THRESHOLD": 1000, "_queue_microphone": upload,
              "_gemini_connected": True, "sd": SimpleNamespace(InputStream=Stream),
              "_mic_statuses": 0,
              "SEND_SAMPLE_RATE": 48000, "CHUNK_SIZE": 480}
        async def scenario():
            with self.assertRaises(TimeoutError):
                await asyncio.wait_for(self.load("listen_audio", ns)(), 0.02)
        asyncio.run(scenario())
        local.feed.assert_called_once()
        upload.assert_not_called()

    def test_local_prompt_overrides_gemini_and_reaches_existing_echo_reference(self):
        import threading
        pcm = b"\x11\x00" * 10
        local = SimpleNamespace(render=Mock(return_value=pcm))
        enhancer = SimpleNamespace(mix_output=lambda chunk: chunk, rendered=Mock())
        ns = {"np": np, "_playback_lock": threading.Lock(), "_playback_buffer": b"\x22\x00" * 10,
              "_offline_fall": local, "_waiting_cue": Mock(), "_audio_enhancer": enhancer,
              "_playback_taken": 0, "monitor": Mock(), "RECEIVE_SAMPLE_RATE": 24000,
              "voice_volume": SimpleNamespace(apply=lambda chunk: chunk), "OUTPUT_CHANNELS": 1}
        output = np.zeros((10, 1), dtype=np.int16)
        self.load("_output_callback", ns)(output, 10, None, None)
        self.assertEqual(output.tobytes(), pcm)
        enhancer.rendered.assert_called_once_with(pcm, None)
        ns["_waiting_cue"].cancel.assert_called_once()

    def test_audio_lifetime_is_independent_of_gemini_reconnects(self):
        async def scenario():
            started = asyncio.Event()
            output = Mock()
            local = Mock()
            local.ready = True
            async def microphone():
                started.set()
                await asyncio.Event().wait()
            async def network():
                await started.wait()
                for _ in range(3):
                    self.assertFalse(output.close.called)
                    self.assertFalse(local.close.called)
                    await asyncio.sleep(0)
                raise asyncio.CancelledError()
            async def forever():
                await asyncio.Event().wait()
            ns = {"asyncio": asyncio, "os": os, "FALL_DETECTION_ENABLED": True,
                  "time": time, "_shutdown_event": threading.Event(),
                  "sd": SimpleNamespace(PortAudioError=RuntimeError), "_RestartAudio": RuntimeError,
                  "fall_worker": SimpleNamespace(), "monitor": Mock(), "_flush_playback": Mock(),
                  "start_output_stream": Mock(return_value=output), "listen_audio": microphone,
                  "_local_fall_monitor": forever, "_run_gemini": network}
            run = self.load("run", ns)
            with patch.object(fall, "Checkin", return_value=local), patch.object(fall, "enabled", return_value=True):
                task = asyncio.create_task(run())
                await started.wait()
                await asyncio.sleep(0.02)
                task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await task
            ns["start_output_stream"].assert_called_once()
            local.close.assert_called_once()
            output.close.assert_called_once()
        asyncio.run(scenario())

    def test_local_monitor_consumes_both_detectors_without_a_session(self):
        async def scenario():
            import threading
            event = threading.Event()
            event.set()
            local = SimpleNamespace(ready=True, trigger=Mock())
            worker = SimpleNamespace(pop_alert=Mock(side_effect=[{"recorded": 1}, None, None]))
            ns = {"asyncio": asyncio, "_offline_fall": local, "_fall_detected_event": event, "fall_worker": worker, "_gemini_connected": False}
            task = asyncio.create_task(self.load("_local_fall_monitor", ns)())
            await asyncio.sleep(0.01)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
            self.assertEqual(local.trigger.call_count, 2)
            self.assertFalse(event.is_set())
        asyncio.run(scenario())

    def test_device_recovery_closes_streams_before_reset_and_restarts(self):
        async def scenario():
            events = []
            restarted = asyncio.Event()
            attempts = 0

            def output():
                events.append("output opened")
                return Mock(stop=lambda: events.append("output stopped"),
                            close=lambda: events.append("output closed"))

            async def microphone():
                try:
                    await asyncio.Event().wait()
                finally:
                    events.append("mic stopped")

            async def network():
                nonlocal attempts
                attempts += 1
                if attempts == 1:
                    raise RuntimeError("device unavailable")
                restarted.set()
                await asyncio.Event().wait()

            async def reset():
                self.assertIn("mic stopped", events)
                self.assertEqual(events[-2:], ["output stopped", "output closed"])
                events.append("reset")

            ns = {"asyncio": asyncio, "os": os, "FALL_DETECTION_ENABLED": False,
                  "time": time, "_shutdown_event": threading.Event(),
                  "sd": SimpleNamespace(PortAudioError=OSError), "_RestartAudio": RuntimeError,
                  "_offline_fall": None, "fall_worker": SimpleNamespace(), "monitor": Mock(),
                  "_flush_playback": Mock(), "start_output_stream": output,
                  "listen_audio": microphone, "_local_fall_monitor": microphone,
                  "_run_gemini": network, "_reset_audio": reset}
            run = self.load("run", ns)
            real_sleep = asyncio.sleep

            async def pause(seconds):
                await real_sleep(0)

            with patch.object(fall, "enabled", return_value=False), patch("asyncio.sleep", pause):
                task = asyncio.create_task(run())
                try:
                    await asyncio.wait_for(restarted.wait(), 1)
                    self.assertFalse(ns["_shutdown_event"].is_set())
                finally:
                    task.cancel()
                    with self.assertRaises(asyncio.CancelledError):
                        await task
            self.assertEqual(events.count("reset"), 1)
            self.assertEqual(events.count("output opened"), 2)
            self.assertEqual(events.count("output closed"), 2)
        asyncio.run(scenario())
