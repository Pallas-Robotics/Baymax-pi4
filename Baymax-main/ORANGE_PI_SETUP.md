# Orange Pi 4 Pro setup

This fork targets the Allwinner A733 Orange Pi 4 Pro, using native Linux ARM64
and Python 3.12. OPI5 development is separate; do not apply Rockchip drivers,
RKNN conversion instructions or another board's tuning results here.

## Installation and devices

Use [OPI4-Flash](../devops/opi4-flash/README.md), the
[SD-card guide](../docs/SD_CARD_FLASH.md), or the existing Debian prerequisites
and [clickables](../devops/clickables/README.md). Native dependencies are in
`requirements-orange-pi.txt`, with no Rockchip runtime package. Operational
channels need initialization/review before building cards with the new repository
defaults. Existing devices retain their saved repository/channel.

`run_mvp.py` owns Setup/Monitor/eyes; `run_pc.py` owns key/model preflight and v10
startup. Select the actual mic, speaker, camera and serial device in Setup.
Starting the connected runtime sends audio/camera context to Gemini and retains
existing local recording. Keep private settings, models and recordings out of Git.

## CPU pose, scheduling and audio

The configured MediaPipe task runs on the CPU in the existing isolated vision
child. Lite and a 10 FPS target remain defaults; configured FPS is not measured
throughput. A failed/hung child is restarted once; repeated failure leaves video
available without claiming working fall detection. Capture timestamps drive fall
velocities, and core/toolkit detection share pose without duplicate check-ins.

`BAYMAX_POSE_BACKEND=auto`, `cpu` and `mediapipe` select MediaPipe. Legacy
accelerator values are unsupported and fall back to CPU with a diagnostic.
Explicit `onnx` is an existing CPU-only development option requiring prepared,
checksummed models. See [pose](features/pose/README.md).

The OS scheduler owns CPU placement. There is no affinity, vision-child priority
or GIL policy. Stale parent settings cannot activate one. Speaker output stays at
1024 frames/default device latency unless the owner explicitly configures bounded
manual settings. Test actual echo and underruns on OPI4. Network reconnects keep
devices alive; device recovery closes them before resetting PortAudio.

## Memory and owner controls

Existing v10 memory storage/data paths remain. ChromaDB and the ONNX Runtime CPU
embedder are memory dependencies, separate from pose. Latest memories are included
in instructions; between-turn notes are opt-in and do not delay a reply. See
[memory](features/memory_palace/README.md) before changing storage/settings.

Shared reconnect, timing, search and conversation fixes are retained without
OPI5 platform policy. Language adaptation and local fall check-ins require
separate owner opt-ins and remain software-tested. Local fall speech also needs
prepared Vosk assets and espeak-ng; see [offline fall](features/toolkits/OFFLINE_FALL.md).

## Validation still required

Follow [TESTING_PROTOCOL.md](TESTING_PROTOCOL.md): OPI4 fresh-card boot, native
imports, actual audio/camera/eyes, echo, offline answers, reconnect, stop/restart,
combined CPU pose load, thermals and rollback remain pending. The
[performance sampler](../devops/performance/README.md) records CPU/RAM/temperature
and speech timing; accelerator load is not applicable. Neither another board's
measurements nor software tests certify this release.
