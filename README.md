# Ember for Orange Pi 4 Pro

This fork is specifically for **Orange Pi 4 Pro (Allwinner A733)**. Its starting
revision is `551f80a`; the reconciliation adds selected shared runtime fixes and
our OPI4 features. OPI5 development belongs in
[Pallas-Robotics/Baymax](https://github.com/Pallas-Robotics/Baymax).

The active OPI4 platform path uses CPU pose processing and the OS scheduler.
There is no Rockchip runtime dependency, RKNN converter, NPU selection, CPU-affinity
policy, GIL tuning or automatic board-specific speaker profile here. The original
histories remain archived; they are not the active platform configuration.

Start with the [working protocol](docs/WORKING_PROTOCOL.md),
[OPI4 setup](Baymax-main/ORANGE_PI_SETUP.md) and
[reconciliation decisions](docs/OPI4_RECONCILIATION.md). This is a draft candidate;
software checks do not establish actual OPI4 operation or release approval.

## Get and start the application

```bash
git clone https://github.com/Pallas-Robotics/Baymax-pi4.git
cd Baymax-pi4
```

For development, use `main` and a feature branch. V1, reviewed on
`opi4-chat-timing`, is merged into `main`. The normal on-board update channel is
`release`.
Complete the board guide's system packages, Python environment, device selection
and Gemini-key setup first. OPI4 uses
`Baymax-main/requirements-orange-pi.txt`.

The device entry point is `Baymax-main/run_mvp.py`, which wraps v10 startup,
device readiness and the eye lifecycle. Setup/Monitor are available through the
[clickables](devops/clickables/README.md) or local `devUI.py`. The runtime needs
connectivity for Gemini conversation; enabling a configured runtime can send
microphone/camera context to Gemini and save local session data. Keep private
keys/settings and runtime data out of Git.

## Features and layout

```text
Baymax-main/          Runtime, setup/debugger and device configuration
  features/          Conversational ability, eyes, pose and grouped toolkits
devops/              Installation, SD builder, graph tools and editing protocol
docs/features/       Organized feature log and Graphify guide
graphify-out/        Interactive graph, report and feature-log viewer
tests/               Overall gate and feature/deployment suite definitions
test/                Standalone chat UI regression check
```

Ember's shared persona follows the speaker's language, follows language switches
and mixed-language speech, and keeps English internal messages from changing the
conversation language. This is model guidance; see the measured limitations below.

Conversation and audio live under `features/conversational_ability`; eyes and pose
have their own packages; toolkits group everyday, family, information and media
behavior. Existing memory/runtime hooks retain their working entry points.
Reserved person-recognition/Memory Palace namespaces are not proof of completed
identity recognition. See the feature log for the precise boundaries.

The chat debugger shows local speech activity before a Gemini transcript,
updating per-turn speech/transcript/reply/playback timings, and one centered
updating bubble per toolkit call. Speech and DAC timings are estimates.

[Multilingual simulations](Baymax-main/evals/languages/README.md) exercise native
conversation, language switches and Hindi-English mixing. The
[language matrix](docs/features/LANGUAGES.md) separates Google's 99 candidate
entries from actual model/config-specific validation; none are claimed validated
until live runs and language/audio review are complete.
The [Pi simulation report](docs/features/OPI4_LANGUAGE_RESULTS.md) records 80/81
automated response runs passing, one Polish switching failure, and separate
synthetic-speech transcription failures. It tested the language instruction in
a temporary copy; the same instruction is now included in `Baymax-main/features/persona.py`.
The running robot was not replaced.

## Orange Pi 4 Pro SD image

The reusable builder is in [devops/opi4-flash](devops/opi4-flash/README.md).
It builds a private, per-card image on a Linux host/VM. Select the runtime branch,
Wi-Fi, Gemini key and time zone; retain the private access file. It does not write
a physical card. Use an image writer's verification step when flashing.
For the build, verification and card-writing walkthrough with the read-only image
verifier, see [SD CARD Flash](docs/SD_CARD_FLASH.md). The 4 Pro image is not a 5 Max image. Fresh-card hardware validation is
separate from checksum and unit tests.

## Tests and future edits

Read [devops/EDITING_PROTOCOL.md](devops/EDITING_PROTOCOL.md) before editing.
Use an environment with the application's test dependencies:

```bash
python tests/run.py                              # full repository validation
python tests/run.py --feature conversational_ability
python tests/run.py --feature eyes --feature pose
python tests/run.py --changed origin/main
```

Feature commands include overall checks. Shared/unknown changes select all
suites. [tests/README.md](tests/README.md) explains ownership, reports and how to
add tests. Existing CI also runs `Baymax-main/check_release.py`; it preserves
separate core/toolkit results and includes root overall checks (the
suite-ownership checks run only in CI and `tests/run.py`, not in a robot's update
gate). Explain skips and platform failures. Passing offline tests is not
permission to merge/deploy or proof of live hardware behavior; use [the live
checklist](Baymax-main/TESTING_PROTOCOL.md).
Full root/deployment CI is provided as a workflow template awaiting a maintainer
with workflow-write access; see the tests guide's CI activation section.

Every feature also follows the [performance protocol](devops/performance/README.md):
compare baseline, feature and combined load for CPU/RAM, NPU telemetry,
temperature and added speech-response latency, with explicit board-specific
budgets. Feature test commands include the sampler's offline checks; actual
measurements run separately on the Orange Pi.

## Graphify

Open [the graph](graphify-out/graph.html) locally after downloading the checkout;
its **Organized feature log** link opens the inventory. GitHub displays HTML as
source. [The guide](docs/features/GRAPHIFY.md) explains regeneration and confidence
limits. Graphify is optional developer documentation, outside the robot runtime.
Private data, recordings, model assets and generated SD images are excluded.
