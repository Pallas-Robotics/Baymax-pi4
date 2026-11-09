# OPI4 CPU pose

The existing camera vision child runs the configured MediaPipe task on the CPU.
`ChildPose` supplies increasing video timestamps and returns landmarks through
`features/vision_process.py`; it never opens another capture stream. Core and
optional toolkit fall detection share this pose.

`BAYMAX_POSE_BACKEND=auto`, `cpu` and `mediapipe` use MediaPipe. Unsupported
legacy accelerator values produce a diagnostic and still select CPU. There is
no Rockchip package, NPU probe, converter or board-specific scheduler.

Explicit `onnx` retains the existing CPU-only comparison pipeline. It requires
prepared checksum-matching ONNX files and a manifest in `BAYMAX_POSE_MODEL_DIR`
(default `.models/pose_cpu`). Unavailable models or inference failures fall back
to MediaPipe. These optional pose assets are separate from the ONNX memory
embedder. Existing asset directories are left intact; an explicit model-directory
setting may still point to prepared CPU assets. Imports neither download assets nor start capture.

Inputs are existing BGR frames and timestamps; outputs are landmarks and CPU
backend state. Processing is local; ordinary camera context sent to Gemini is
unchanged. The watchdog bounds frame/model waits. A failed CPU child is restarted
once; another failure leaves video-only operation. `benchmark.py` and `validate.py`
are CPU-only offline development tools using supplied clips/models, not capture
or accuracy certification.

Run the root pose suite and full release gate for shared-runtime changes. Tests
cover CPU selection, stale accelerator overrides, timestamps, failures, landmark
math and bounded child recovery. See [validation](VALIDATION.md).
