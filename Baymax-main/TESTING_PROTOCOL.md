# Ember testing and review protocol

Start with the [mandatory working protocol](../docs/WORKING_PROTOCOL.md) and
[contribution route](../CONTRIBUTING.md). Pallas-Robotics/Baymax-pi4 publishes Ember; device
owners use an approved deploy revision, while contributors review a draft PR
from a feature branch targeting main. Existing deploy behavior takes priority.

## Validation stages and promotion authority

1. **Experimental:** unvalidated bench development, owner opt-in only.
2. **Software:** automated core/toolkit/regression tests and direct synthetic
   inputs. Injecting landmarks or PCM on an Orange Pi is still this stage.
3. **Simulation:** the chamber shows known footage to the real camera and replays
   known audio into the real microphone; record expected/actual outputs.
4. **Hardware:** controlled safe physical trials on the named board, OS, models
   and peripherals, with resource/latency and recovery evidence.
5. **Deploy:** the software lead reviews the relevant evidence and approves the
   exact source revision. CI or a directory name cannot grant this approval.

Language adaptation and offline fall check-ins remain software-only until the
chamber and physical checks are recorded. Keep their stages in
[experimental features](features/experimental/README.md) current. A behavior,
model or audio/camera change requires rerunning affected evidence. Never mark
pending, skipped or failed checks as passed.

Every PR records source revision, commands/results, known regressions, failures,
skips, data flows, dependencies and rollback/data compatibility. New work must
preserve working deployed features. Follow [channel policy](../docs/UPDATE_CHANNELS.md):
owner channel selection is independent of feature opt-in; synchronization of
approved deploy fixes happens through reviewed GitHub PRs, not on-device merges.

Before submitting, rebuild changed protocol sources and run
`python devops/graphify/check.py` from the repository root. The graph must point
to these rules before implementation details.

Every feature PR must verify both the core runtime and the relevant toolkits. Authors test and provide evidence; the software lead reviews the results and decides whether to approve. An offline pass is not deployment approval.

## 1. Run the offline gate

From `Baymax-main`, use the installed environment interpreter:

```powershell
# Windows
.\.venv\Scripts\python.exe check_release.py --report .local-review/report.md
```

```bash
# macOS/Linux
.venv/bin/python check_release.py --report .local-review/report.md
```

This runs all `tests/test_*.py`, prints separate core and toolkit results, and generates a fresh manual checklist. Exit code 0 requires both sections to contain tests and pass; failures or missing required test files return 1. No API key, capture or live service is needed. The checks test the shipped defaults: while they run, this machine's `BAYMAX_*`/`EMBER_*` settings and API keys are out of the environment and its `.env` reads as empty, so a robot's own settings cannot fail them (a test that needs a setting sets it). Reports overwrite the chosen path, so save completed evidence separately before rerunning. `.local-review/` is ignored by Git.

Core checks cover configuration, UI protections, hardware selection, upstream runtime parity and monitor behavior. Toolkit checks cover mocked location/weather behavior, caching, ambiguity, failures and Gemini tool-response routing. The runner also has regression tests for its failure/report behavior. These tests were added for this desktop implementation; they are not a full Baymax suite.

## 1b. Optional: Gemini-in-the-loop checks before the robot

`python evals/live_eval.py --dry-run`, then without `--dry-run`, plays synthetic speech and pictures into Ember's real MVP Gemini session and checks transcripts, tool calls, replies and reply latency over several runs (`evals/README.md`). It needs `GOOGLE_API_KEY` and sends only the listed synthetic data. Paste the summary table into the PR as Gemini-behaviour evidence; it does not replace the robot checks below.

## 2. Complete live core checks

Use the report's core checklist: fresh setup, startup key/model verification (a rejected key must stop before capture), actual device tests, spoken Gemini conversation, multiple turns, interruption, live monitor, stop/restart and core conversation with toolkits disabled. Run these deliberately: `run_pc.py` sends microphone/camera data to Gemini and the upstream runtime records audio locally. Never let the offline CLI start capture automatically.

Record what was tested, actual results, commit, date, OS, devices and runtime baseline. Record failures as failures and untested items as pending. Only mark N/A with a reason. Check platform/deployed-hardware claims on those actual targets; Windows success does not establish macOS/Linux or robot compatibility.

## 3. Complete toolkit and integration checks

Use the report's location/weather checklist, including city correction, ambiguity, units, provider accuracy/time, other-city weather, grouped monitor events and conversation after a tool call. Exercise slow/unavailable services. Mocked failures in the offline suite do not prove live recovery.

Each added or changed toolkit needs its own README, offline tests named `tests/test_toolkit*.py`, and PR checklist covering normal inputs, invalid/ambiguous inputs, failures/timeouts, core integration and disabled behavior. Describe dependencies and external data flows. New tests are discovered automatically; maintaining meaningful coverage is the author's and reviewer's responsibility.

## 4. Submit evidence for review

Use the PR template and update `CHANGELOG.md`. Include separate core and toolkit results and a sanitized copy of the completed checklist. Do not include keys, private transcripts or recordings. James reviews pending checks and any exceptions before approving. Repository checks/branch protection are separate administrative configuration; this CLI does not enforce GitHub merge permissions.
