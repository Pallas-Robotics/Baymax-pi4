# OFFLINE Speech — software evidence

Author: **natey**. Target: **Orange Pi 4 Pro / Allwinner A733, CPU**.
Source base: `Pallas-Robotics/Baymax-pi4` `main` at
`551f80a8fec73f8e19bf5948255152dd1380822d`. Feature branch:
`feature/offline-speech`. The PR identifies the feature revision; tests below ran
on its application/test files before finalizing this evidence document.

## Implemented boundary

Whisper tiny/base CPU-int8 and bundled Silero VAD v6 run in a dedicated speech
subprocess. An existing cleaned-mic tap feeds bounded queues. Local transcripts
carry monotonic utterance timestamps and matching camera/pose/fall metadata;
absent or stale context is unknown. Existing Gemini, recordings, vision/fall
behavior and channel pointers are preserved. The feature defaults off and needs
explicit model preparation and owner opt-in. No additional hardware stream,
NPU backend, caregiver notification or data-schema migration is introduced.

This is a local ASR sidecar. Gemini still handles conversation, and the existing
shared mic session still depends on the Gemini runtime connection. Reconnects
interrupt capture and discard old-session local results. A standalone offline
conversation/capture service is outside this PR. See the
[feature guide](../../Baymax-main/features/offline_speech/README.md).

## Tests — 2026-11-10, Windows x86_64 / Python 3.12.15

| Check | Observed result |
|---|---|
| Speech unit/native suite in isolated optional environment | 24 passed; real bundled Silero loaded and processed streaming silence; no skips |
| Actual v10 mic/camera/Monitor integration harness | 3 passed; cleaned PCM tap, preserved raw recording, timestamped metadata, separate local events |
| Public WAV through real tiny CPU subprocess | Passed expected-fragment smoke check; zero dropped packets/utterances/stale results |
| Public WAV through real base CPU subprocess | Passed expected-fragment smoke check; zero dropped packets/utterances/stale results |
| Combined Orange Pi + speech dependency resolution, ARM64/Python 3.12 | Passed; NumPy 1.26.4, protobuf 4.25.9 and tokenizers 0.22.2 retained |
| `python check_release.py` candidate | Core: 568 run, 1 failure, 2 errors, 5 skips; toolkit: 241 run, 3 failures, no skips. **FAIL**, same six failure/error test cases as base |
| Same gate on clean, unchanged `main` | Core: 541 run, 1 failure, 2 errors, 4 skips; toolkit: 241 run, 3 failures, no skips. **FAIL** |
| `git diff --check` / Python source parsing | Passed |

The native speech tests use an isolated environment, separate from the existing
application test environment. The full gate deliberately runs without optional
speech packages; its extra skip is the native Silero test, which passed separately.
These are Windows results, not native ARM execution or combined-load benchmarks.
The existing base has no Graphify entry-point tooling or root suite registry;
this feature follows its existing `check_release.py` and source-based workflow.

### Existing gate failures reproduced on unchanged main

- `PoseModelDownloadTests.test_a_cut_download_is_not_taken_for_the_model` and
  `test_the_download_lands_in_shared_and_the_link_stays`: Windows symlink
  privilege errors.
- `DownloadTests.test_cleanup_keeps_the_original_error_when_the_partial_file_is_gone`
  in `test_semantic_embedder`: Windows open-file/delete semantics.
- `DownloadCacheTests.test_a_file_still_in_use_is_left_for_the_next_track`,
  `test_each_track_replaces_the_last_and_another_program_clears_the_old_one`, and
  `test_the_track_already_cached_is_not_downloaded_again` in
  `test_toolkit_audiobooks`: existing Windows path assertions.

Existing four core skips: optional Chroma integration, two explicitly selected
real memory-model tests, and converted pose parity assets. No failures or skips
were suppressed. Full logs remain ignored local review artifacts; the public
record contains no keys, private sessions or recordings.

### Native model and sample provenance

Public sample: [whisper.cpp `samples/jfk.wav`](https://github.com/ggml-org/whisper.cpp/blob/master/samples/jfk.wav),
used as file input only. No microphone, camera, API key or inference provider was
used for these native speech checks. Both models loaded from prepared local
directories with offline Hub settings, CPU int8, one decoding thread.

| Artifact | SHA-256 |
|---|---|
| Systran/faster-whisper-tiny `model.bin` | `dcb76c6586fc06cbdac6dd21f14cfd129cc4cdd9dce19bf4ffa62e59cbe6e6d1` |
| Systran/faster-whisper-base `model.bin` | `d01c3014881c9c6f3133c182f3d2887eb6ca1c789a7538c5c007196857a0a6a9` |
| Public `jfk.wav` | `59dfb9a4acb36fe2a2affc14bacbee2920ff435cb13cc314a08c13f66ba7860e` |

The expected fragment was `country`. **This is a transport/native-inference
smoke check, not an accuracy pass.** Tiny misrecognized one short phrase as
“Knock!” and base omitted that phrase in the initial run. End-to-end speech
accuracy, short answers, endpoint tuning and language detection need a reviewed
corpus. Local results are not used to make fall-alert decisions.

## Pending approval evidence

- [ ] Native ARM64 install/import and model preparation on the actual A733.
- [ ] Owner opt-in and normal on-device speech with real cleanup/speaker echo.
- [ ] Chamber audio/video replay with expected/actual speech and safe fall cases.
- [ ] Baseline/off, active/on and combined speech + camera + fall CPU/RAM/thermal,
      pose FPS, queue-drop and p95 latency budgets. Record NPU telemetry as
      unavailable if unsupported; no NPU use is claimed.
- [ ] Network/camera loss, missing models, decode failure, timeout, stop/restart
      and old-session result isolation on the board.
- [ ] GitHub platform checks reviewed and software-lead review before merge;
      deployment/promotion separately.

No robot, SD image, service, release branch or installed settings were changed.
Disable via `EMBER_OFFLINE_SPEECH=0` and restart; existing data remains compatible.
