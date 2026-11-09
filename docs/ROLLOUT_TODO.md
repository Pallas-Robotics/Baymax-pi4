# Release rollout checklist

Repository authority: Pallas-Robotics/Baymax-pi4. `deploy` is reserved for an approved baseline; feature
PRs target `main`. See [working protocol](WORKING_PROTOCOL.md).

Review: [draft PR #1](https://github.com/Pallas-Robotics/Baymax-pi4/pull/1), targeting this fork’s main.

## Prepared in this draft

- [x] Document the authority chain, branch/PR route, stable-feature priority and
  software → chamber → physical → lead-approved release evidence.
- [x] Classify language adaptation and offline fall check-ins as software-only,
  with individual owner opt-ins and repeated unresolved fall questions.
- [x] Require Graphify-first LLM work in AGENTS and provide a protocol-first query.
- [x] Build a source-linked public map and add a CI gate for protocol freshness.
- [x] Offer five named owner channel choices in the SD-image settings menu.
- [x] Keep the work in a draft PR; do not promote it to deployed devices.

## Next, after review / when owners are available

- [ ] Review and merge the draft with the software lead; investigate failing CI
  rather than treating active workflows or running jobs as a passing gate.
- [ ] Verify automatic push-triggered CI end to end. Manual runs were observed
  on all four initial channels; push-run records had not appeared during setup.
- [ ] Configure required-review/status-check branch protection and a named release
  maintainer; branch names alone do not enforce readiness.
- [ ] Implement reviewed synchronization PRs from deploy to testing branches.
  Do not auto-merge or force-push. Design bot authentication so sync PRs actually
  trigger required CI; a GitHub Actions token can suppress follow-on events.
- [ ] Complete chamber replay and physical audio/video/room trials. Record exact
  source, board, models, fixtures, peripherals, expected/actual outputs and misses.
- [ ] Validate stable-feature regression coverage, update failures, loss of power,
  offline startup, last-known-good rollback and stored-data downgrade compatibility.
- [ ] Add installed commit/update/health/last-good status where missing; keep owner
  channel and individual experiment switches visible and persistent.
- [ ] Test owner channel switching without resetting credentials/preferences or
  interrupting an active conversation/check-in, then canary a small bench group.
- [ ] Deliberately migrate each existing Ember's source/channel after approval.
  Existing devices are not redirected merely by changing this repository.

Human chamber/physical evidence, owner choices, new credentials/security access
and software-lead approval cannot be supplied by an unattended coding session.

- [ ] Seed/configure operational channels in Baymax-pi4 before building cards with its new defaults; historical channel refs are preserved under `archive/natey/*`.
- [ ] Verify installed devices no longer depend on NateyKim/Baymax before deleting the old fork.
