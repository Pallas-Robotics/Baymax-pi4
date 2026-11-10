# Joe's changes on the OPI4 baseline

This candidate starts from our original `opi4-chat-timing` (`54ee70e`), which
contains our existing timing/language work above the fork's main. It does not
include the rejected reconciliation branch or merge the separate
`offline-fall-checkin` development line. The installed OPI4 revision observed
before testing was `e5a4bd7`; its live release and settings are preserved.

## Source attribution

Joe Kojima authored the following changes. The language and cache commits retain
his author and `cherry picked from` provenance. Reconnect compatibility changes
adapt his implementation instead of copying the newer OPI5 runtime.

| Source | Included behavior |
|---|---|
| [51f15f1](https://github.com/Pallas-Robotics/Baymax/commit/51f15f158b3a1686e06492544d2b0bacba489337) | English offline pause phrases during other-language conversation |
| [2d50ced](https://github.com/Pallas-Robotics/Baymax/commit/2d50ced7a10d1a1fd00673ef67bf03b6fe9a6d4d) | Judge language by words, preserve script/accent handling, suppress spoken system tags |
| [ee940fa](https://github.com/Pallas-Robotics/Baymax/commit/ee940fa9f7f29680fe012ab363122df1197b3a29) | Weather/location refresh and quiet family-profile delivery |
| [30c7d7b](https://github.com/Pallas-Robotics/Baymax/commit/30c7d7bbef5b24b7d89ed92810f0428ce14c16d3) | Fast network retry without a global audio reset |
| [7f21fab](https://github.com/Pallas-Robotics/Baymax/commit/7f21fab4c71827529f9095c58aeb07993ab6faca) | Preserve resume handles for connections that never started |
| [c3deba5](https://github.com/Pallas-Robotics/Baymax/commit/c3deba5810e17f9ae4f8a575022acd3ceb03c895) | Treat DNS/network OSErrors as transport failures |

Our integration rechecks quietness after profile loading and retries failed,
cancelled or deferred profile delivery without clearing concurrent edits.
The weather worker skips periodic requests while the toolkit is disabled.
Existing language scenarios remain in `evals/languages/`; absent scenarios from
Joe's separate scenario catalog were not pulled into the main eval catalog.

## Compatibility and external requests

No model, device selection, audio rate, speech-end sensitivity, turn-end silence,
existing memory database, recording configuration or production alert setting
is changed. Existing per-connection audio cleanup remains in place. Network
retries omit the old device-release delay; device/unknown errors keep the reset
and its 2/5-second delays, awaited rather than blocking the event loop.

Weather refreshes every 9 minutes and IP-derived location every 54 minutes while
the toolkit is enabled. This adds periodic requests to existing Open-Meteo and
IPWho providers; confirmed locations skip IP refresh. Disabling the toolkit
prevents future periodic refresh calls, checked at the next worker tick. The
worker ends with the process. No new dependency or provider is added.

Separate search sessions, newer memory scheduling, proactive GoAway handover,
OPI5/NPU configuration and the separate offline-fall experiment are excluded.

## Validation

On 2026-11-10, the isolated OPI4 run used Linux 6.6.98-vendor-sun60iw2 and
Python 3.12.15, with the installed release's Python environment:

- `python check_release.py`: core 587 tests, zero failures/errors, 5 skipped;
  toolkit 251 tests, zero failures/errors/skips; exit 0.
- `python tests/run.py`: 880 tests across 16 passing suites, 5 skipped; the
  person-recognition namespace is explicitly N/A (0 tests); exit 0.
- Skips: ChromaDB integration unavailable, two real-memory-model tests without
  an explicitly selected model directory, pose parity without converted assets,
  and Node unavailable for the Linux chat UI check. Windows overall/graph checks
  include a passing Node chat UI check.
- Windows focused reconnect tests: 19 passed; family 12 passed; session 13
  passed; language/config 16 passed; graph/overall/performance 29 passed.
- Windows full gate: failed in two symlink-permission tests, a Windows file-lock
  test and three audiobook path-separator tests. These remain visible platform
  limitations, rather than being suppressed or called passing. The Linux gate
  passes those paths.

Tested source tree: `479180f4e566fec9b02f92f661e133ec40c40a91`.
Its public archive SHA256 was
`37cbad68e697bed32ea47c43324e5bd518ffcb9bc4fc00363b6e331f32157126`,
verified both before upload and on the board. Subsequent evidence/documentation
updates do not change the application/test blobs in that tested tree.
See the [sanitized reports](evidence/joe-opi4-software-20261110.md).

No microphone/camera capture or live Gemini calls are made by the offline gate.
Spoken multilingual behavior, real disconnect/resumption, combined-load resource
budgets, chamber replay and physical validation remain pending. An isolated
software run on the board is software evidence, not physical validation.

The candidate can be discarded without changing the live robot. No database
migration or release-channel change is needed to test or roll it back.
