# Ember development instructions

## Mandatory working protocol

- Before repository analysis or edits, run `python devops/graphify/query.py "<actual question>"` and read its protocol/source output. Then follow `docs/WORKING_PROTOCOL.md`, `CONTRIBUTING.md` and `Baymax-main/TESTING_PROTOCOL.md`. Report unavailable tooling rather than claiming it was used.
- Pallas-Robotics/Baymax-pi4 is the publishing authority; branch from its main and submit a draft PR back to main. Preserve deploy behavior. Never promote, force-push channels, switch owners, or certify hardware from software tests. The software lead approves releases.
- Keep Graphify protocol sources and their generated map current; CI runs `python devops/graphify/check.py`. Documentation requirements apply to human and LLM contributions.

- Follow `docs/UPDATE_CHANNELS.md` and `Baymax-main/features/experimental/README.md`. Experiments are off unless the owner opts in per feature. Language adaptation and offline fall check-ins remain `tested_in_software` until chamber video/audio replay evidence exists; injected data on a Pi alone is software testing. Preserve sim/hardware evidence and lead release review.

- Follow `devops/EDITING_PROTOCOL.md` for future edits and `tests/README.md` for
  overall/feature validation. Keep suite ownership and the feature log current.

- The documented desktop entry point is `Baymax-main/run_pc.py`, using the version-10 runtime. Confirm the actual hardware entry point before claiming deployed parity.
- Preserve the base conversation prompt, Gemini models, audio sample rates and processing. Organize core systems under `Baymax-main/features/`: `memory_palace/`, `person_recognition/`, and callable capabilities in `toolkits/`. Put OS/device changes in `pc_hardware.py`.
- Do not open extra microphone/camera streams in toolkit features. Do not commit credentials, recordings, runtime snapshots, local databases or virtual environments.
- Each feature needs a README explaining inputs, outputs, dependencies, external data flows, enabling/disabling and tests.
- Run tests from `Baymax-main`: `python -m unittest discover -s tests`. Hardware, Gemini and provider tests require explicit knowledge of the data sent; do not start listening just to verify the UI.
- Review branches are approved by the software lead before merging/deploying. Do not change the robot's systemd startup or enable production alerts as part of desktop setup.

- Every feature PR follows `Baymax-main/TESTING_PROTOCOL.md`: run `python check_release.py`, provide separate core/toolkit/live integration evidence, update `CHANGELOG.md`, and explain pending checks. New toolkit tests use `tests/test_toolkit*.py`. Offline success never grants release approval.
