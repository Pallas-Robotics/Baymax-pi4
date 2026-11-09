"""OPI4 CPU pose backends. Auto uses MediaPipe; ONNX is an explicit CPU-only option.

No board detection, accelerator runtime, CPU affinity or NPU conversion is used.
The normal camera runs ChildPose in the existing isolated vision process.
"""
import os
from pathlib import Path
import time
import traceback

from features.pose import models
from features.vision_process import loading_model

ENV_BACKEND = "BAYMAX_POSE_BACKEND"
CPU_NAME = "CPU (MediaPipe)"
ONNX_NAME = "CPU (ONNX Runtime)"
_CONFIDENCES = {"min_pose_detection_confidence": "min_detection_confidence",
                "min_pose_presence_confidence": "min_presence_confidence",
                "min_tracking_confidence": "min_tracking_confidence"}




def _log(message):
    print(f"[POSE] {message}", flush=True)


def default_mediapipe_options(model_path):
    """The camera's PoseLandmarker settings: ChildPose (realtime_gemini_10.py's pose
    process) uses them for MediaPipe on the CPU, and benchmark.py/validate.py too. VIDEO
    mode is required (MediaPipeCpuBackend calls detect_for_video). The ONNX port's
    PosePipeline defaults are the same 0.5 confidences."""
    from mediapipe.tasks import python as mp_tasks
    from mediapipe.tasks.python import vision
    return vision.PoseLandmarkerOptions(
        base_options=mp_tasks.BaseOptions(model_asset_path=str(model_path)),
        running_mode=vision.RunningMode.VIDEO, num_poses=1,
        min_pose_detection_confidence=0.5, min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5)


class _Backend:
    name = ""
    device = ""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


class MediaPipeCpuBackend(_Backend):
    """MediaPipe PoseLandmarker on the CPU: the calls the camera thread always made."""
    name = CPU_NAME
    device = "CPU"

    def __init__(self, options):
        import mediapipe as mp
        from mediapipe.tasks.python import vision
        self._mp = mp
        self._landmarker = vision.PoseLandmarker.create_from_options(options)

    def detect(self, frame_bgr, timestamp_ms):
        import cv2
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb)
        detection = self._landmarker.detect_for_video(mp_image, timestamp_ms)
        return detection.pose_landmarks[0] if detection.pose_landmarks else None

    def close(self):
        self._landmarker.close()


class PipelineBackend(_Backend):
    """features.pose.pipeline on an engine (ONNX Runtime on the CPU).
    confidences: PosePipeline's min_*_confidence keywords (default 0.5 each)."""

    def __init__(self, engine, name, device, **confidences):
        from features.pose.pipeline import PosePipeline
        self.engine = engine
        self.name = name
        self.device = device
        self.pipeline = PosePipeline(engine, **confidences)

    def detect(self, frame_bgr, timestamp_ms):
        return self.pipeline.detect(frame_bgr, timestamp_ms)

    def close(self):
        self.engine.close()


class FallbackBackend(_Backend):
    """The ONNX backend, replaced by MediaPipe on the CPU if it ever raises."""

    def __init__(self, primary, cpu_factory, log=_log):
        self.active = primary
        self.cpu_factory = cpu_factory
        self.log = log

    @property
    def name(self):
        return self.active.name

    @property
    def device(self):
        return self.active.device

    def detect(self, frame_bgr, timestamp_ms):
        try:
            return self.active.detect(frame_bgr, timestamp_ms)
        except Exception as error:
            if self.cpu_factory is None:
                raise
            failed = self.active
            self.log(f"{failed.name} failed during inference ({type(error).__name__}: {error}); "
                     f"switching to {CPU_NAME} for the rest of this run.")
            self.log("Traceback of that failure:\n" + "".join(traceback.format_exception(error)).rstrip())
            self.cpu_factory, factory = None, self.cpu_factory
            try:
                failed.close()
            except Exception:
                pass
            # In the pose child this frame now imports and loads MediaPipe (1.2-1.3 s on the
            # CPU backend when cached, longer from a cold SD card): the start's limit, not 5 s.
            loading_model()
            self.active = factory()
            return self.active.detect(frame_bgr, timestamp_ms)

    def close(self):
        self.active.close()


def _flat(text):
    return " ".join(str(text).split())


def pipeline_confidences(mediapipe_options):
    """The confidences the runtime gives MediaPipe, as PosePipeline keywords, so the port
    and its MediaPipe fallback decide alike. Missing or invalid ones (not in 0..1) keep 0.5."""
    confidences = {}
    for option, keyword in _CONFIDENCES.items():
        try:
            value = getattr(mediapipe_options, option, None)
        except Exception:
            continue
        if isinstance(value, (int, float)) and not isinstance(value, bool) and 0.0 <= value <= 1.0:
            confidences[keyword] = float(value)
    return confidences


def _open_onnx(env, confidences):
    from features.pose.engines import OnnxEngine
    directory = models.model_dir(env)
    paths = models.verified_files(directory, models.load_manifest(directory), "onnx")
    engine = OnnxEngine(paths["pose_detector"], paths["pose_landmarks_detector"])
    return PipelineBackend(engine, ONNX_NAME, "CPU", **confidences)


def _warm_up(engine):
    import numpy as np
    boxes, scores = engine.detector(np.zeros((224, 224, 3), np.uint8))
    raw, flag, heatmap = engine.landmarks(np.zeros((256, 256, 3), np.uint8))
    if not (np.isfinite(boxes).all() and np.isfinite(raw).all() and np.isfinite(flag).all()):
        raise RuntimeError("warm-up inference returned non-finite values")


def weights_warning(mediapipe_options=None, model_path=None):
    """A warning when the runtime's full .task (MediaPipe, the fallback) holds other weights
    than the ones the converted models were made from (e.g. Google changed 'latest').
    None for a lite or heavy .task, which is a different model by choice."""
    try:
        path = model_path or getattr(getattr(mediapipe_options, "base_options", None), "model_asset_path", None)
        # Only a full .task can match: lite or heavy is a different network on purpose
        # (the ONNX backend always runs the checked full models; the lite .task is the CPU fallback).
        if not path or not Path(path).name.startswith("pose_landmarker_full"):
            return None
        if models.task_matches_pinned(path) is not False:
            return None
    except Exception:
        return None
    return (f"{Path(path).name} has different weights from the converted models (models.TFLITE_SHA256), "
            f"so the port and MediaPipe (the fallback) may disagree")


def _close_quietly(backend):
    try:
        backend.close()
    except Exception:
        pass


def _warn(log, warnings):
    for warning in warnings:
        if warning:
            log(f"Warning: {warning}.")

def create_pose_backend(mediapipe_options=None, model_path=None, env=None, log=_log,
                        cpu_factory=None):
    """Select only CPU implementations; unsupported legacy accelerator choices use MediaPipe."""
    env = os.environ if env is None else env
    if cpu_factory is None:
        def cpu_factory():
            options = mediapipe_options if mediapipe_options is not None else default_mediapipe_options(model_path)
            return MediaPipeCpuBackend(options)
    choice = env.get(ENV_BACKEND, "auto").strip().lower() or "auto"
    if choice == "onnx":
        try:
            backend = _open_onnx(env, pipeline_confidences(mediapipe_options))
        except Exception as error:
            log(f"Pose backend: {CPU_NAME}. ONNX Runtime skipped: {type(error).__name__}: {error}")
        else:
            log(f"Pose backend: {ONNX_NAME}.")
            _warn(log, [weights_warning(mediapipe_options, model_path)])
            return FallbackBackend(backend, cpu_factory, log)
    elif choice not in ("auto", "cpu", "mediapipe"):
        log(f"Unsupported {ENV_BACKEND}={choice!r} in the OPI4 fork; using {CPU_NAME}.")
    log(f"Pose backend: {CPU_NAME}.")
    return cpu_factory()


class ChildPose:
    """CPU pose in the vision child, with strictly increasing video timestamps."""
    def __init__(self, model_path, cpu_factory=None):
        self.backend = create_pose_backend(model_path=model_path, cpu_factory=cpu_factory)
        self.timestamp = -1

    name = property(lambda self: self.backend.name)
    device = property(lambda self: self.backend.device)

    def detect(self, frame_bgr):
        self.timestamp = max(self.timestamp + 1, int(time.monotonic() * 1000))
        return self.backend.detect(frame_bgr, self.timestamp)

    def close(self):
        self.backend.close()
