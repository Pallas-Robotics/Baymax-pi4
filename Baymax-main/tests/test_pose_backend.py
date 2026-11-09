"""features/pose: backend choice, MediaPipe-graph math, smoothing and wiring. Offline:
no models, no NPU, no camera. Parity with MediaPipe runs only when converted models,
onnxruntime, mediapipe and the sample image are present, and is skipped otherwise."""
import ast
import functools
import inspect
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import numpy as np

from features.pose import backend, engines, models, pipeline as P
from features.pose.engines import split_detector, split_landmarks, heatmap_hwc
import pc_hardware

ROOT = Path(__file__).resolve().parents[1]
TAU = 2 * math.pi


class Opi4CpuBackendTests(unittest.TestCase):
    def test_auto_uses_cpu_without_accelerator_detection_or_model_loading(self):
        cpu = Mock(device="CPU")
        with patch.object(backend, "_open_onnx") as onnx:
            selected = backend.create_pose_backend(env={"BAYMAX_POSE_BACKEND": "auto",
                "BAYMAX_POSE_NPU_CORE": "all", "BAYMAX_FAST_CPUS": "4,5,6,7"},
                cpu_factory=lambda: cpu, log=Mock())
        self.assertIs(selected, cpu)
        onnx.assert_not_called()

    def test_accelerator_overrides_cannot_select_an_accelerator(self):
        for choice in ("npu", "rknn", "rk3588", "invalid"):
            with self.subTest(choice=choice):
                cpu, log = Mock(device="CPU"), Mock()
                with patch.object(backend, "_open_onnx") as onnx:
                    self.assertIs(backend.create_pose_backend(env={backend.ENV_BACKEND: choice},
                        cpu_factory=lambda: cpu, log=log), cpu)
                onnx.assert_not_called()
                self.assertIn("Unsupported", log.call_args_list[0].args[0])

    def test_explicit_onnx_is_cpu_only_and_unavailable_models_fall_back(self):
        cpu = Mock(device="CPU")
        with patch.object(backend, "_open_onnx", side_effect=RuntimeError("missing CPU model")):
            self.assertIs(backend.create_pose_backend(env={backend.ENV_BACKEND: "onnx"},
                cpu_factory=lambda: cpu, log=Mock()), cpu)

    def test_explicit_onnx_failure_closes_it_and_uses_mediapipe(self):
        onnx = Mock(device="CPU", name="ONNX")
        onnx.detect.side_effect = RuntimeError("bad CPU inference")
        cpu = Mock(device="CPU")
        cpu.detect.return_value = "landmarks"
        with patch.object(backend, "_open_onnx", return_value=onnx), \
                patch.object(backend, "weights_warning", return_value=None):
            selected = backend.create_pose_backend(env={backend.ENV_BACKEND: "onnx"},
                cpu_factory=lambda: cpu, log=Mock())
        self.assertEqual(selected.detect("frame", 10), "landmarks")
        self.assertEqual(selected.device, "CPU")
        onnx.close.assert_called_once()
        cpu.detect.assert_called_once_with("frame", 10)

    def test_child_keeps_monotonic_timestamps_and_closes_cpu_model(self):
        cpu = Mock(device="CPU")
        with patch.object(backend.time, "monotonic", side_effect=[1, 1, 0.5]):
            child = backend.ChildPose("lite.task", cpu_factory=lambda: cpu)
            for _ in range(3):
                child.detect("frame")
        self.assertEqual([call.args[1] for call in cpu.detect.call_args_list], [1000, 1001, 1002])
        self.assertEqual(child.device, "CPU")
        child.close()
        cpu.close.assert_called_once()

    def test_opi4_dependency_profile_has_no_rockchip_runtime(self):
        requirements = (ROOT / "requirements-orange-pi.txt").read_text()
        packages = [line for line in requirements.splitlines() if line and not line.startswith("#")]
        self.assertFalse(any("rknn" in package.lower() for package in packages))

    def test_legacy_scheduling_settings_cannot_change_opi4_cpu_or_gil(self):
        with patch.dict(os.environ, {"BAYMAX_CPU_PINNING": "on", "BAYMAX_GIL_SWITCH_MS": "1",
                                    "BAYMAX_FAST_CPUS": "4,5,6,7"}), \
                patch.object(os, "sched_setaffinity", create=True) as affinity, \
                patch.object(sys, "setswitchinterval") as gil:
            self.assertIsNone(pc_hardware.use_performance_cpus())
        affinity.assert_not_called()
        gil.assert_not_called()


class FakeEngine:
    """Detector finds nothing unless told; landmark model returns a fixed pose."""

    def __init__(self, detection=None, flag=0.9, landmarks=None):
        self.detection = detection
        self.flag = flag
        self.raw = landmarks
        self.detector_calls = 0
        self.landmark_calls = 0
        self.closed = False

    def detector(self, crop):
        assert crop.shape == (224, 224, 3) and crop.dtype == np.uint8
        self.detector_calls += 1
        boxes = np.zeros((2254, 12), np.float32)
        scores = np.full((2254, 1), -10.0, np.float32)
        if self.detection is not None:
            index, raw = self.detection
            boxes[index] = raw
            scores[index] = 5.0
        return boxes, scores

    def landmarks(self, crop):
        assert crop.shape == (256, 256, 3) and crop.dtype == np.uint8
        self.landmark_calls += 1
        raw = self.raw if self.raw is not None else standing_raw()
        return raw, np.array([self.flag], np.float32), np.full((64, 64, 39), -10.0, np.float32)

    def close(self):
        self.closed = True


def standing_raw():
    """39 landmarks in 256-px crop units: an upright figure; aux 33 at the hips, 34 above the head."""
    raw = np.zeros((39, 5), np.float32)
    raw[:, 0], raw[:, 1] = 128, 128
    raw[:, 3], raw[:, 4] = 4.0, 4.0                     # sigmoid -> 0.982
    raw[0, :2] = (128, 60)
    raw[11, :2], raw[12, :2] = (150, 90), (106, 90)
    raw[23, :2], raw[24, :2] = (140, 150), (116, 150)
    raw[33, :2], raw[34, :2] = (128, 150), (128, 50)
    return raw.reshape(-1)


def centred_detection(width=640, height=480):
    """Raw detector output on the anchor nearest the image centre, keypoints 0/1 at the
    hips and above the head, 100 px apart vertically in the 224 input."""
    anchors = P.ssd_anchors()
    index = int(np.argmin(np.hypot(anchors[:, 0] - 0.5, anchors[:, 1] - 0.5)))
    raw = np.zeros(12, np.float32)
    raw[2:4] = 80                                       # w, h in 224 px
    raw[4:6] = (0, 30)                                  # keypoint 0 (x, y) relative to the anchor
    raw[6:8] = (0, -70)                                 # keypoint 1
    return index, raw


class AnchorAndRoiTests(unittest.TestCase):
    def test_anchor_count_and_layout(self):
        anchors = P.ssd_anchors()
        self.assertEqual(anchors.shape, (2254, 2))
        self.assertTrue(np.allclose(anchors[0], (0.5 / 28, 0.5 / 28)))
        self.assertTrue(np.allclose(anchors[1], anchors[0]))           # two anchors per cell at stride 8
        self.assertTrue(np.allclose(anchors[1568], (0.5 / 14, 0.5 / 14)))
        self.assertTrue(np.allclose(anchors[1960:1966], (0.5 / 7, 0.5 / 7)))   # six at the three stride-32 layers
        self.assertTrue(np.allclose(anchors[-1], (6.5 / 7, 6.5 / 7)))

    def test_letterbox_of_the_camera_frame(self):
        roi, padding = P.detector_roi(640, 480)
        self.assertEqual(roi, (320.0, 240.0, 640.0, 640.0, 0.0))
        self.assertEqual(padding, (0.0, 0.125, 0.0, 0.125))
        roi, padding = P.detector_roi(480, 640)
        self.assertEqual(roi[2:4], (640.0, 640.0))
        self.assertEqual(padding, (0.125, 0.0, 0.125, 0.0))
        detection = P.Detection(0.9, (0.25, 0.125, 0.75, 0.875), [(0.5, 0.125), (0.5, 0.875), (0, 0), (0, 0)])
        clean = P.remove_letterbox(detection, (0.0, 0.125, 0.0, 0.125))
        self.assertTrue(np.allclose(clean.box, (0.25, 0.0, 0.75, 1.0)))
        self.assertTrue(np.allclose(clean.keypoints[:2], [(0.5, 0.0), (0.5, 1.0)]))

    def test_upright_person_roi(self):
        # Hips at the centre, keypoint 1 120 px above them on a 640x480 frame.
        rect = P.alignment_rect((0.5, 0.5), (0.5, 0.25), 640, 480)
        self.assertAlmostEqual(rect.rotation, 0.0)
        self.assertAlmostEqual(rect.width, 240 / 640)
        self.assertAlmostEqual(rect.height, 240 / 480)
        roi = P.transform_rect(rect, 640, 480)
        self.assertAlmostEqual(roi.width * 640, 300.0)                # x1.25, square in pixels
        self.assertAlmostEqual(roi.height * 480, 300.0)
        self.assertEqual((roi.x_center, roi.y_center), (0.5, 0.5))

    def test_lying_person_roi_is_rotated(self):
        rect = P.alignment_rect((0.5, 0.5), (0.75, 0.5), 640, 480)     # head to the right
        self.assertAlmostEqual(rect.rotation, math.pi / 2)
        rect = P.alignment_rect((0.5, 0.5), (0.25, 0.5), 640, 480)     # head to the left
        self.assertAlmostEqual(rect.rotation, -math.pi / 2)
        rect = P.alignment_rect((0.5, 0.5), (0.5, 0.75), 640, 480)     # upside down
        self.assertAlmostEqual(abs(rect.rotation), math.pi)
        for angle in (-7.0, -math.pi, 0.0, 3.5, 12.0):
            value = P.normalize_radians(angle)
            self.assertTrue(-math.pi <= value < math.pi)
            self.assertAlmostEqual(math.cos(value), math.cos(angle))

    def test_decode_weighted_nms_and_association(self):
        anchors = P.ssd_anchors()
        boxes = np.zeros((2254, 12), np.float32)
        scores = np.full((2254, 1), -10.0, np.float32)
        a, b, c = 300, 301, 1000                                       # a/b share a cell; c is elsewhere
        boxes[a, 2:4] = boxes[b, 2:4] = boxes[c, 2:4] = 40
        boxes[b, 0] = 2.0                                              # b shifted 2 px right
        boxes[a, 4:6] = (0, 10)
        boxes[b, 4:6] = (2, 10)
        scores[a], scores[b], scores[c] = 2.0, 0.0, 1.0
        scores[5] = -0.1                                               # sigmoid < 0.5: dropped
        detections = P.decode_detections(boxes, scores, anchors, 0.5)
        self.assertEqual(len(detections), 3)
        self.assertAlmostEqual(detections[0].box[2] - detections[0].box[0], 40 / 224, places=6)
        merged = P.weighted_nms(detections)
        self.assertEqual(len(merged), 2)
        wa, wb = 1 / (1 + math.exp(-2.0)), 0.5
        expected_x = anchors[a, 0] + (wb * 2.0 / 224) / (wa + wb)
        self.assertAlmostEqual(merged[0].keypoints[0, 0], expected_x, places=6)
        self.assertAlmostEqual(merged[0].score, wa, places=6)          # the top score is kept
        self.assertAlmostEqual(merged[1].keypoints[0, 0], anchors[c, 0], places=6)
        first = P.Rect(0.5, 0.5, 0.2, 0.2)
        overlapping = P.Rect(0.51, 0.5, 0.2, 0.2)
        apart = P.Rect(0.1, 0.1, 0.1, 0.1)
        self.assertEqual(P.associate([first, apart, overlapping], 0.5), [apart, overlapping])


class LandmarkMathTests(unittest.TestCase):
    def test_decode_uses_crop_pixels_and_sigmoid(self):
        raw = np.zeros((39, 5), np.float32)
        raw[0] = (128, 64, 25.6, 0.0, 2.0)
        out = P.decode_landmarks(raw.reshape(-1))
        self.assertTrue(np.allclose(out[0], (0.5, 0.25, 0.1, 0.5, 1 / (1 + math.exp(-2)))))

    def test_projection_onto_a_rotated_roi(self):
        landmarks = np.array([[0.5, 0.5, 0.1, 1, 1], [1.0, 0.5, 0.0, 1, 1], [0.5, 0.0, 0.0, 1, 1]])
        rect = P.Rect(0.4, 0.6, 0.5, 0.25, 0.0)
        out = P.project(landmarks, rect)
        self.assertTrue(np.allclose(out[0, :3], (0.4, 0.6, 0.05)))      # centre; z scales like x
        self.assertTrue(np.allclose(out[1, :2], (0.65, 0.6)))
        out = P.project(landmarks, P.Rect(0.4, 0.6, 0.5, 0.25, math.pi / 2))
        self.assertTrue(np.allclose(out[1, :2], (0.4, 0.725)))          # crop's right edge points down
        self.assertTrue(np.allclose(out[2, :2], (0.65, 0.6)))           # crop's top points right

    def test_heatmap_refinement(self):
        landmarks = np.zeros((39, 5))
        landmarks[:, :2] = 0.5
        landmarks[1, :2] = (-0.2, 0.5)                                  # outside: untouched
        heatmap = np.full((64, 64, 39), -10.0, np.float32)
        heatmap[30, 34, 0] = 10.0                                       # one confident cell near (32, 32)
        heatmap[:, :, 2] = 0.0                                          # sigmoid 0.5 everywhere: refined to the window centre
        heatmap[:, :, 3] = -1.0                                         # sigmoid 0.27 < 0.5: not refined
        out = P.refine_from_heatmap(landmarks.copy(), heatmap)
        self.assertAlmostEqual(out[0, 0], 34 / 64, places=3)
        self.assertAlmostEqual(out[0, 1], 30 / 64, places=3)
        self.assertTrue(np.allclose(out[1, :2], (-0.2, 0.5)))
        self.assertTrue(np.allclose(out[2, :2], (32 / 64, 32 / 64)))
        self.assertTrue(np.allclose(out[3, :2], (0.5, 0.5)))

    def test_engine_outputs_by_size_and_layout(self):
        boxes, scores = split_detector([np.zeros((1, 2254, 1)), np.ones((1, 2254, 12))])
        self.assertEqual((boxes.shape, scores.shape, boxes[0, 0], scores[0, 0]), ((2254, 12), (2254, 1), 1.0, 0.0))
        nhwc = np.arange(64 * 64 * 39, dtype=np.float32).reshape(1, 64, 64, 39)
        self.assertTrue(np.array_equal(heatmap_hwc(nhwc.transpose(0, 3, 1, 2)), nhwc[0]))
        raw, flag, heatmap = split_landmarks([nhwc, np.full((1, 1), 0.7), np.zeros((1, 195))])
        self.assertEqual((raw.shape, float(flag[0]), heatmap.shape), ((195,), np.float32(0.7), (64, 64, 39)))
        with self.assertRaises(RuntimeError):
            split_landmarks([np.zeros((1, 195))])


class SmoothingTests(unittest.TestCase):
    def test_one_euro_matches_mediapipe_rules(self):
        f = P.OneEuro(min_cutoff=0.05, beta=80.0, derivate_cutoff=1.0)
        self.assertEqual(float(f.apply(1_000_000, np.array([10.0]), 1.0)[0]), 10.0)      # first value passes
        self.assertEqual(float(f.apply(1_000_000, np.array([99.0]), 1.0)[0]), 99.0)      # same timestamp: raw
        still = f.apply(1_066_000_000, np.array([10.0]), 1.0)
        self.assertAlmostEqual(float(still[0]), 10.0)
        jump = float(f.apply(1_132_000_000, np.array([11.0]), 0.01)[0])
        self.assertTrue(10.0 < jump < 11.0)                                              # a small move is smoothed
        fast = P.OneEuro(0.05, 80.0, 1.0)
        fast.apply(1_000_000, np.array([10.0]), 1.0)
        self.assertGreater(float(fast.apply(67_000_000, np.array([11.0]), 1.0)[0]), jump)  # a big scaled move follows faster

    def test_visibility_survives_lost_tracking_but_positions_restart(self):
        smoother = P.LandmarkSmoother()
        rect = P.Rect(0.5, 0.5, 0.5, 0.5)
        pose = np.zeros((33, 5))
        pose[:, :2] = 0.5
        pose[:, 3] = 1.0
        smoother.apply(pose, 1000, 640, 480, rect)
        smoother.reset_position()                       # a frame without a pose
        moved = pose.copy()
        moved[:, 0] = 0.6
        moved[:, 3] = 0.0
        out = smoother.apply(moved, 200_000, 640, 480, rect)
        self.assertTrue(np.allclose(out[:, 0], 0.6))    # positions start over
        self.assertTrue(np.allclose(out[:, 3], 0.9))    # visibility: 0.1 * 0 + 0.9 * 1

    def test_tiny_roi_is_not_filtered(self):
        smoother = P.LandmarkSmoother()
        pose = np.full((33, 5), 0.5)
        out = smoother.apply(pose, 1000, 640, 480, P.Rect(0.5, 0.5, 0.0, 0.0))
        self.assertTrue(np.allclose(out, pose))


class PipelineFlowTests(unittest.TestCase):
    frame = np.full((480, 640, 3), 90, np.uint8)

    def test_detect_then_track_then_lose(self):
        engine = FakeEngine(detection=centred_detection())
        pose = P.PosePipeline(engine)
        first = pose.detect(self.frame, 10)
        self.assertEqual(len(first), 33)
        self.assertTrue(pose.detector_ran)
        landmark = first[0]
        for attribute in ("x", "y", "z", "visibility", "presence"):
            self.assertIsInstance(getattr(landmark, attribute), float)
        self.assertAlmostEqual(landmark.visibility, 1 / (1 + math.exp(-4.0)), places=5)
        # Upright: the nose is above the hips, shoulders above hips.
        self.assertLess(first[0].y, first[23].y)
        self.assertLess(first[11].y, first[23].y)
        self.assertEqual(engine.detector_calls, 1)
        second = pose.detect(self.frame, 76)
        self.assertFalse(pose.detector_ran)              # tracked from the auxiliary landmarks
        self.assertEqual(engine.detector_calls, 1)
        self.assertAlmostEqual(second[11].x, first[11].x, delta=0.01)   # new ROI, same person
        engine.flag = 0.4                                # pose flag below 0.5: lost
        self.assertIsNone(pose.detect(self.frame, 142))
        engine.flag = 0.9
        pose.detect(self.frame, 208)
        self.assertEqual(engine.detector_calls, 2)       # re-detected on the next frame

    def test_nothing_found(self):
        engine = FakeEngine()
        pose = P.PosePipeline(engine)
        self.assertIsNone(pose.detect(self.frame, 1))
        self.assertIsNone(pose.detect(self.frame, 2))
        self.assertEqual((engine.detector_calls, engine.landmark_calls), (2, 0))

    def test_timestamps_must_increase(self):
        pose = P.PosePipeline(FakeEngine())
        pose.detect(self.frame, 5)
        with self.assertRaises(ValueError):
            pose.detect(self.frame, 5)

    def test_tracking_roi_follows_the_auxiliary_landmarks(self):
        engine = FakeEngine(detection=centred_detection())
        pose = P.PosePipeline(engine)
        pose.detect(self.frame, 1)
        upright = pose.tracking_rect
        self.assertIsNotNone(upright)
        self.assertAlmostEqual(upright.rotation, 0.0, places=5)
        lying = standing_raw().reshape(39, 5).copy()
        lying[34, :2] = (228, 150)                        # keypoint above the head now to the right
        engine.raw = lying.reshape(-1)
        pose.detect(self.frame, 70)
        self.assertAlmostEqual(abs(pose.tracking_rect.rotation), math.pi / 2, delta=0.3)


class ToolSettingsTests(unittest.TestCase):
    def test_validate_judges_falls_with_the_runtimes_settings(self):
        from features.pose import validate
        source = (ROOT / "realtime_gemini_10.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        constants = {node.targets[0].id: ast.literal_eval(node.value) for node in tree.body
                     if isinstance(node, ast.Assign) and len(node.targets) == 1
                     and isinstance(node.targets[0], ast.Name) and node.targets[0].id.startswith("FALL_")
                     and isinstance(node.value, ast.Constant)}
        expected = dict(angle_threshold=constants["FALL_ANGLE_THRESHOLD"],
                        ang_vel_threshold=constants["FALL_ANG_VEL_THRESHOLD"],
                        hip_vel_threshold=constants["FALL_HIP_VEL_THRESHOLD"],
                        history_window=constants["FALL_HISTORY_FRAMES"],
                        confirmation_frames=constants["FALL_CONFIRMATION_FRAMES"],
                        cooldown_seconds=constants["FALL_COOLDOWN_SECONDS"],
                        stay_down_s=constants["FALL_STAY_DOWN_SECONDS"])
        self.assertEqual(validate.FALL_SETTINGS, expected)
        self.assertEqual(constants["FALL_DETECTION_FPS"], 10)
        # validate.py's --fps default is the camera thread's rate (stop main() right after parsing).
        import argparse
        parsed = {}
        real = argparse.ArgumentParser.parse_args
        def stop_after_parsing(parser, *args, **kwargs):
            parsed.update(vars(real(parser, *args, **kwargs)))
            raise SystemExit(0)
        with patch.object(argparse.ArgumentParser, "parse_args", stop_after_parsing), self.assertRaises(SystemExit):
            validate.main(["--task", "t", "--onnx-dir", "d"])
        self.assertEqual(parsed["fps"], constants["FALL_DETECTION_FPS"])


class ParityWithMediaPipeTests(unittest.TestCase):
    """Needs converted ONNX models, onnxruntime, mediapipe, the .task and the converter's
    cached sample image; skipped when any is missing (e.g. in CI or on a fresh checkout)."""

    def test_port_matches_mediapipe_on_the_sample_image(self):
        directory = models.model_dir()
        image_path = directory / "build" / "pose.jpg"
        tasks = [ROOT / "pose_landmarker_full.task", ROOT / ".models" / "pose_landmarker_full.task",
                 directory / "build" / "pose_landmarker_full.task"]
        task = next((t for t in tasks if t.is_file()), tasks[0])
        try:
            import onnxruntime  # noqa: F401
            import mediapipe  # noqa: F401
            import cv2
            paths = models.verified_files(directory, models.load_manifest(directory), "onnx")
        except (ImportError, models.ModelError) as error:
            self.skipTest(f"parity needs converted models and runtimes: {error}")
        if not image_path.is_file() or not task.is_file():
            self.skipTest("parity needs the converter's sample image and the runtime's .task")
        from features.pose.engines import OnnxEngine
        image = cv2.imread(str(image_path))
        cpu = backend.MediaPipeCpuBackend(backend.default_mediapipe_options(task))
        port = backend.PipelineBackend(OnnxEngine(paths["pose_detector"], paths["pose_landmarks_detector"]), "port", "CPU")
        try:
            for timestamp in (1, 67, 133):
                a, b = cpu.detect(image, timestamp), port.detect(image, timestamp)
                self.assertIsNotNone(a)
                self.assertIsNotNone(b)
                error = [math.hypot(p.x - q.x, p.y - q.y) for p, q in zip(a, b)]
                self.assertLess(float(np.median(error)), 0.003)
                self.assertLess(max(error), 0.02)
                self.assertEqual([p.visibility >= 0.5 for p in a], [q.visibility >= 0.5 for q in b])
        finally:
            cpu.close()
            port.close()
