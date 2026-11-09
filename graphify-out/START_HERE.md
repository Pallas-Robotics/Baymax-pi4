# Ember working protocol — start here

This protocol governs human and LLM contributions to **Pallas-Robotics/Baymax-pi4**. Read it
before changing code or giving architecture advice. Repository authority is this
fork; `deploy` is reserved for its approved runtime baseline. Historical channels are archived during migration; see docs/UPDATE_CHANNELS.md before building or installing. A branch name is not test evidence.

## Authority and change route

1. The device owner chooses its repository/channel and opts in to each experiment.
2. Contributors develop on a focused feature branch from current `main`, push to
   Pallas-Robotics/Baymax-pi4 and open a draft PR targeting `main`. Never push feature work
   directly to `deploy` or a testing channel. Upstream JoeKojima/Pallas changes
   enter through the same reviewed route.
3. CI supplies software evidence. Reviewers assess behavior, regressions, scope,
   data flows and compatibility. Chamber and physical evidence require recorded
   trials, not a green CI badge. The software lead (James, or an explicitly named
   delegate) approves release promotion. Automation cannot grant that approval.
4. A release maintainer promotes the exact approved revision. Ordinary owners
   consume `deploy`; reviewers use a PR checkout. See [channel policy](UPDATE_CHANNELS.md).

Use `git fetch origin`, `git switch main`, `git pull --ff-only origin main`, then
`git switch -c feature/<short-name>` in a clean checkout whose origin is
`https://github.com/Pallas-Robotics/Baymax-pi4.git`. Preserve dirty work before switching.
Use `git push -u origin feature/<short-name>` and target this fork's `main` in the
PR. If your origin is upstream, add this fork as a separate remote and use its
name consistently. Do not silently rewrite another contributor's remotes.

## Stable behavior takes priority

All candidates must preserve working deployed features. Add a focused regression
case for a behavior change; run the required core/toolkit gate as well as feature
checks. Failures stay visible. A change with known regressions is not promoted
because a new experiment works. Experiments default off, and selecting a test
channel does not enable them.

Approved `deploy` fixes must flow into testing branches through synchronization
PRs, followed by CI and conflict review. Do this on GitHub/in development, never
by making a robot merge two branches. Automated synchronization may open PRs;
it must not force-push, silently discard experimental work or bypass approval.
Automatic sync-PR creation is a rollout task, not an existing guarantee.

## Five owner modes and four validation boundaries

| Owner mode / branch | Meaning |
|---|---|
| Experimental / `experimental` | Unvalidated development baseline; bench use only |
| Software test / `needssoftwaretest` | Candidate undergoing software validation |
| Sim test / `needssimtest` | Software evidence accepted; awaiting chamber replay |
| Hardware test / `needshardwaretest` | Chamber evidence accepted; awaiting physical trials |
| Deploy / `deploy` | Relevant hardware evidence reviewed and release approved |

Feature records track their highest completed stage separately from the selected
device channel. Language adaptation and offline fall check-ins remain **tested
in software**. Direct landmark/PCM injection on an Orange Pi is software testing.
Simulation means your chamber replays known video through the real camera and
audio through the real mic, with expected/actual outputs recorded. Hardware
validation adds safe physical scenarios under real conditions on a named board,
OS, model and peripheral setup. Do not ask anyone to perform an unsafe fall.

## Required evidence and professional PRs

Follow [TESTING_PROTOCOL.md](../Baymax-main/TESTING_PROTOCOL.md). A reviewable PR
states the concrete problem/result, scope, source commit, tests and exact results,
skips/failures, data leaving the device, model/dependency changes, rollback/data
compatibility, and the sim/hardware checks still pending. Attach sanitized
evidence. Never commit keys, private audio/transcripts, databases or recordings.
No fabricated passes, blanket platform claims, unrelated refactors, automatic
production-alert activation or deployment disguised as testing.

Evidence is tied to a revision and setup. Behavior/model/camera/audio changes
invalidate the affected evidence until retested. An owner should be able to see
channel, installed commit, enabled experiments, update state and last known-good
version. Updates should preserve credentials/preferences and stop safely during
network/power loss. Verify actual rollback and data-schema compatibility before
fleet rollout. These owner/health controls are tracked rollout work where absent.

## Mandatory Graphify entry point for LLM work

Before code analysis or edits, run:

```bash
python devops/graphify/query.py "<the actual question>"
```

It prints this protocol's required entry points before invoking Graphify. Read
the returned source locations and then inspect only the relevant code. Graph
relationships are navigation/evidence, not permission to ignore source or change
scope. Rebuild with `python devops/graphify/build.py` when protocol sources change;
`python devops/graphify/check.py` rejects a missing/stale protocol map in CI.
If Graphify is unavailable, report that limitation, read this protocol directly,
and restore the documented tooling before claiming graph-backed analysis.

Repository instructions require this workflow; CI checks the published protocol
map. Neither can physically control an external LLM or prove that a person read it.
