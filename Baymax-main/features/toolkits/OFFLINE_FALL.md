# Local fall check-ins (v10)

Enabled fall detection can now ask for and record a spoken confirmation without
Gemini or Wi-Fi. This is an English, fixed-phrase check-in, not a local chatbot.
When local dependencies are ready, this path handles check-ins both online and
offline, avoiding two competing questions. It does not contact caregivers or
emergency services.

## Prepare the board while online

From `Baymax-main`, in the installed Python environment:

```bash
sudo apt-get install espeak-ng
.venv/bin/python -m features.toolkits.offline_fall --prepare
.venv/bin/python -m features.toolkits.offline_fall --check
```

The Orange Pi Python profile already includes Vosk. `--prepare` downloads its
existing small English model (~41 MB) from alphacephei.com into the ignored
`models/` folder. `--check` makes no network request. Both commands load the
recognizer and synthesize fixed prompts without opening a microphone, camera or
speaker. The Debian prerequisite script and new SD builds include espeak-ng;
existing boards must install it. Prepare the Vosk model in each checkout, or
retain the existing shared `models/` directory across releases. Pose models must
also be cached before offline startup; the pose feature's setup remains required.

Keep normal saved microphone/speaker/camera configuration and a configured Gemini
key. Enable the normal detector (`fall_detection.enabled` in device.toml) or the
optional toolkit (`BAYMAX_FALL_DETECTION_ENABLED=1`).
In Setup, explicitly opt in under **Experimental features**, or set
`BAYMAX_OFFLINE_FALL_CHECKIN_ENABLED=1`. Default is `0` (off); `0` uses
Gemini-only check-ins. This feature is classified as **tested in software**. Disabled detection does not start the local worker. V8 remains Gemini-only.
Missing Vosk/model/espeak-ng reports local check-ins unavailable and leaves the
existing Gemini check-in path available when connected. No confirmation is assumed.

## Behavior and data flow

- Camera inference and detection stay local. The local monitor consumes events
  from either v10's core detector or the optional toolkit without a Gemini session.
- The existing single mic and output stream outlive network reconnects. Playback
  pauses; disengaged listening reengages. The check-in takes speaker priority and
  uses the existing echo reference and volume setting. No additional device opens.
- Local espeak-ng synthesizes fixed prompts once in memory at startup. Vosk
  receives bounded, recent, echo-cleaned 48 kHz mic chunks resampled to 16 kHz.
  It starts listening after prompt playback and an 800 ms echo guard. Prompt audio,
  stale chunks, partial recognition and previous questions cannot confirm a fall.
- Say **“No, I'm okay”**, **“No, I am okay”**, **“I am okay”**, **“I'm okay”**, or **“I am fine”** to record
  `confirmed_ok`. This records the person's report; it does not establish that
  they are uninjured. Say **“I need help”**, **“help me”**, **“I am not okay”**,
  to record `help_requested`. **“Yes, I've fallen”** or **“Yes, I have fallen”** records `fall_confirmed`, which confirms the event rather than safety. A bare “yes” or “no” is ambiguous and does not resolve the check-in. Only complete, exact final phrases with
  every recognized word at confidence >= 0.85 count. “Yes” or “okay” alone do not
  dismiss the check-in.
- Each question leaves a 15-second listening window. Unclear speech keeps that
  window open; its expiry records `unresolved` and repeats the fixed question.
  Repetition continues until an explicit answer, feature/runtime shutdown, or
  an actual dependency/speaker failure. Silence never means safety. Help/fall
  acknowledgements explicitly say nobody has been contacted. A stalled speaker
  marks local speech unavailable.
  Duplicate detections within the active check-in or 30 seconds of its start
  do not restart it. Acknowledgements finish before normal audio resumes.
  Offline prompts say the online service cannot be reached, rather than guessing
  whether Wi-Fi itself is the cause. Connected prompts do not claim an outage.
  Fixed prompts are synthesized once into reusable local PCM clips, without an LLM.
- State and outcome appear in the existing monitor's `offline_fall_checkin`
  metrics and compact fall events. No raw transcript is added by this feature.
  Outage audio and local answer audio are not queued for later upload. Existing
  session audio recording remains in effect; regular connected conversation and
  camera context still go to Gemini as before.
- An already configured runtime can start after a network-only preflight failure;
  invalid/rejected credentials still stop startup. The Gemini session retries in
  the background. No-key first-time setup is unchanged.

## Validation

`tests/test_toolkit_offline_fall.py` covers synthetic answers, negation, ambiguity,
partial/low-confidence results, echo timing, stale audio, bounded queues,
duplicates, dependency failures, timeouts, audio lifetime, both detectors and
shutdown. Existing preflight/reconnect tests cover offline startup and online
recovery. Run `python check_release.py` from `Baymax-main` for the full gate.

Live checks remain required on each board: prepare, start with Wi-Fi disabled,
trigger with consented prerecorded/safe test input, answer naturally at expected
distance, verify recognition/volume/latency under concurrent pose load, disconnect
mid-question, reconnect after each outcome, test media/disengagement, remove a
dependency, and stop/restart. Measure missed responses, false confirmations,
CPU/RAM and added conversation latency. Do not ask anyone to perform an unsafe
fall. Synthetic tests do not establish speech accuracy or hardware readiness.

## Orange Pi 4 Pro software injection test, 2026-11-07

An isolated test ran on the board's real Python 3.12.15/ARM64 environment, using
real Vosk and espeak-ng. Synthetic pose landmarks triggered the actual detector.
Synthetic US-English speech correctly produced `confirmed_ok` for “No, I'm okay”,
`fall_confirmed` for “Yes, I've fallen”, and `help_requested` for “I need help”
and “I am not okay”. Accelerated silence timers remained unresolved and active
through five prompts. Python socket connects were denied throughout that process;
an explicit Gemini connection probe was blocked, with no further connect attempts.

This is not physical microphone/speaker/camera or real fall-video validation.
The normal Ember service stayed active, its release was not changed, and the
board's network remained connected for that service. Sources/model were staged
under `/home/ember/.cache/ember-offline-fall-trial`, outside the active release.
The Vosk model and espeak-ng test voices are synthetic inputs, not human speech
accuracy evidence. The test identified duplicate “ok”/“okay” grammar spellings
splitting confidence; removing “ok” fixed the synthesized “No, I'm okay” result
without lowering the >=0.85 acceptance threshold.
