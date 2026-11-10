# OFFLINE Speech

**Feature author: natey. Target: Orange Pi 4 Pro (Allwinner A733), CPU.**
Optional local speech detection and transcription alongside the existing vision,
pose and fall pipeline. Default: **off**. This is a software-tested draft;
OPI4 performance, chamber replay and physical validation remain pending.

## Behavior and synchronization

- The existing v10 microphone callback taps its cleaned mono PCM. It never opens
  another mic. The existing camera stays with the vision/fall pipeline.
- A separate speech subprocess runs **Silero VAD v6 (ONNX Runtime)** and
  multilingual **Whisper tiny or base (faster-whisper/CTranslate2, CPU int8)**.
  No NPU is selected. One decoding worker uses one CPU thread by default; two
  are an explicit option. The OS schedules the speech and vision children;
  this does not reserve a physical core or promise simultaneous throughput.
- Silero retains streaming state on 512-sample/32 ms windows at 16 kHz. The
  worker low-pass filters/resamples the existing 48 kHz stream continuously.
  It retains 160 ms of pre-roll, requires 160 ms of speech and endpoints after
  400 ms of silence. Continuous speech splits at 12 seconds. Thresholds 0.5/0.35
  provide start/end hysteresis. No model executes on the capture callback.
- Decoding runs on a separate thread inside the speech child so VAD can keep
  consuming PCM. The parent input queue holds at most 24 packets; the decoder
  holds one pending utterance. Overload drops work, counts it, and resets
  segmentation across packet gaps instead of joining unrelated audio. PCM over
  one second old, queued utterances over five seconds old and results over
  thirty seconds old are discarded. Reconnect changes the generation, so old
  session results cannot appear in a new session.
- Camera capture and audio use the same monotonic clock. Each local transcript
  includes its utterance interval and the latest available vision metadata
  captured within that interval (or within 500 ms before it). Fall detections
  within the matching interval are retained. Frames after the utterance and
  context older than 500 ms at its end are excluded. Missing/stale vision is
  `null`, not a claim that no fall occurred. This correlates events; it does not
  identify who spoke, validate a fall, or change fall alerts/check-ins.
- Speech results remain separate from Gemini transcript deltas. Local events
  appear in Monitor's conversation/event feed and structured results under
  `capabilities.offline_speech` in the local runtime snapshot. The last 20 local
  results are retained in RAM/the existing local status snapshot. They are not
  injected as duplicate Gemini user turns or uploaded by this feature.

## Install and opt in

From `Baymax-main`, in the existing Python 3.12 environment:

```bash
python -m pip install -r requirements-orange-pi.txt -r requirements-offline-speech.txt
python -m features.offline_speech.prepare --model tiny
# Optional second model, selected on the next restart:
python -m features.offline_speech.prepare --model base
```

Preparation explicitly contacts Hugging Face for the public converted Whisper
model (`Systran/faster-whisper-tiny` or `Systran/faster-whisper-base`). Silero's
ONNX model ships in faster-whisper's package. Preparation loads both native
models and reports readiness; models/cache stay in ignored `.models/offline-speech/`.
No models or audio are committed. Package/model downloads need connectivity.

Set private `.env`, then restart the normal `run_mvp.py` entry point:

```dotenv
EMBER_OFFLINE_SPEECH=1
EMBER_OFFLINE_SPEECH_MODEL=tiny
EMBER_OFFLINE_SPEECH_THREADS=1
EMBER_OFFLINE_SPEECH_LANGUAGE=
```

Only `tiny`/`base` and 1/2 CPU threads are accepted. Empty language enables
automatic detection; a language code such as `en` can reduce ambiguity. Runtime
uses local-only model loading and offline Hub settings. A missing model/library,
load/decode failure or watchdog timeout reports an error for speech while the
existing runtime continues. Restart Ember to retry. Set
`EMBER_OFFLINE_SPEECH=0` and restart to disable; no schema/data migration is needed.

The tap requires healthy existing audio cleanup (`BAYMAX_AUDIO_ENHANCEMENT=1`,
already enabled by the normal launcher). It discards audio while the speaker
and its echo tail are active, or when cleanup is unavailable/failed. Existing
engage/disengage and media gates still apply. Speech over Ember's reply is
intentionally omitted from local ASR; Gemini keeps its existing interruption
behavior. Acoustic echo rejection still needs board testing.

**Offline applies to recognition computation.** The existing runtime still
requires Gemini configuration/connectivity to start its shared mic session and
send camera/audio. Its mic session ends during reconnects; this PR does not add
an independent offline capture loop or offline conversational model. Existing
raw recordings, Gemini data flows, prompts, memory, services and update channels
are preserved. The speech child itself makes no external inference requests,
stores no extra audio and receives no images, credentials or identity data in
its IPC messages (its environment still inherits normal process settings).

## Checks and evidence

```bash
python -m unittest discover -s tests -p test_offline_speech.py
python -m features.offline_speech.check --wav /path/to/public-or-synthetic.wav --model tiny --expect country
python -m features.offline_speech.check --wav /path/to/public-or-synthetic.wav --model base --expect country
python check_release.py --report .local-review/offline-speech-gate.md
```

The WAV check requires mono PCM16 at 16/48 kHz, paces input through the actual
speech subprocess and opens no devices. It never downloads a model. Supply
public/synthetic material; do not commit private audio or output transcripts.
The unit suite has one native Silero test skipped when optional packages are
absent; run it in the speech environment too. See
[validation evidence](../../../docs/features/OFFLINE_SPEECH.md).

Before approval: measure baseline/off, speech/on, and combined speech + camera +
fall workloads on the A733 with the actual mic/speaker. Record parent/child CPU,
RAM, temperature, unavailable NPU telemetry, dropped work, pose FPS, speech and
reply latency against explicit budgets. Replay speech/noise, short answers,
multiple languages, speaker echo and safe positive/negative fall scenarios;
check camera loss, model failure, network reconnect and stop/restart. File
injection and Windows tests do not establish chamber/hardware performance or
recognition accuracy. Tiny can misrecognize short isolated words.

## Dependencies and sources

- [Whisper models and MIT license](https://github.com/openai/whisper).
- [faster-whisper 1.2.1](https://github.com/SYSTRAN/faster-whisper/tree/v1.2.1)
  (MIT); its bundled Silero VAD and streaming ONNX input contract are used here.
- [Silero VAD](https://github.com/snakers4/silero-vad) (MIT), a CPU-capable
  speech/non-speech model compatible with 16 kHz Whisper input.
- [CTranslate2 CPU/AArch64 support](https://opennmt.net/CTranslate2/installation.html).

Optional dependencies are separate from the shipped Orange Pi installer.
`setuptools==80.9.0` retains `pkg_resources`, imported by CTranslate2 4.6.
Existing NumPy/SciPy/ONNX Runtime pins are preserved by the combined install.
