"""CPU ONNX pose inference and output-shape validation."""
import numpy as np

# Input value ranges of the two TFLite models (their metadata's mean/std):
# detector (x - 127.5) / 127.5, landmarks (x - 0) / 255.
NORMALIZATION = {
    "pose_detector": {"mean": 127.5, "std": 127.5, "size": 224},
    "pose_landmarks_detector": {"mean": 0.0, "std": 255.0, "size": 256},
}
DETECTOR_BOXES = 2254 * 12
DETECTOR_SCORES = 2254
LANDMARK_VALUES = 195
HEATMAP_VALUES = 64 * 64 * 39


def _by_size(outputs, *sizes):
    """Pick outputs by element count (engines may return them in any order)."""
    found = {}
    for output in outputs:
        array = np.asarray(output)
        if array.size in sizes and array.size not in found:
            found[array.size] = array
    missing = [size for size in sizes if size not in found]
    if missing:
        shapes = [np.asarray(o).shape for o in outputs]
        raise RuntimeError(f"Unexpected pose model outputs {shapes}; missing sizes {missing}")
    return [found[size] for size in sizes]


def heatmap_hwc(heatmap):
    """(64, 64, 39) whatever layout the engine returned (NHWC or NCHW)."""
    heatmap = np.asarray(heatmap, np.float32)
    if heatmap.ndim == 4 and heatmap.shape[1] == 39 and heatmap.shape[3] == 64:
        heatmap = heatmap.transpose(0, 2, 3, 1)
    return heatmap.reshape(64, 64, 39)




def _finite(name, *arrays):
    """A broken engine (e.g. non-finite model output) raises here, so the backend
    falls back to MediaPipe instead of passing NaN/inf on to the pipeline and the UI."""
    for array in arrays:
        if not np.isfinite(array).all():
            raise RuntimeError(f"{name} returned non-finite values")
    return arrays


def split_detector(outputs):
    boxes, scores = _by_size(outputs, DETECTOR_BOXES, DETECTOR_SCORES)
    return _finite("pose detector", np.asarray(boxes, np.float32).reshape(2254, 12),
                   np.asarray(scores, np.float32).reshape(2254, 1))


def split_landmarks(outputs):
    raw, flag, heatmap = _by_size(outputs, LANDMARK_VALUES, 1, HEATMAP_VALUES)
    return _finite("pose landmark model", np.asarray(raw, np.float32).reshape(LANDMARK_VALUES),
                   np.asarray(flag, np.float32).reshape(1), heatmap_hwc(heatmap))


class OnnxEngine:
    """ONNX Runtime on the CPU (validation, and BAYMAX_POSE_BACKEND=onnx)."""
    name = "ONNX Runtime (CPU)"

    def __init__(self, detector_path, landmarks_path, threads=None):
        import onnxruntime as ort
        options = ort.SessionOptions()
        if threads:
            options.intra_op_num_threads = int(threads)
        self.sessions = {}
        for key, path in (("pose_detector", detector_path), ("pose_landmarks_detector", landmarks_path)):
            session = ort.InferenceSession(str(path), options, providers=["CPUExecutionProvider"])
            shape = session.get_inputs()[0].shape
            self.sessions[key] = (session, session.get_inputs()[0].name, shape[1] == 3)

    def _run(self, key, crop):
        session, input_name, nchw = self.sessions[key]
        norm = NORMALIZATION[key]
        # Same arithmetic as MediaPipe's convertTo(dst, CV_32F, scale, offset).
        scale = np.float32(1.0 / norm["std"])
        offset = np.float32(-norm["mean"] / norm["std"])
        tensor = crop.astype(np.float32)[None] * scale + offset
        if nchw:
            tensor = tensor.transpose(0, 3, 1, 2)
        return session.run(None, {input_name: np.ascontiguousarray(tensor)})

    def detector(self, crop):
        return split_detector(self._run("pose_detector", crop))

    def landmarks(self, crop):
        return split_landmarks(self._run("pose_landmarks_detector", crop))

    def close(self):
        self.sessions = {}
