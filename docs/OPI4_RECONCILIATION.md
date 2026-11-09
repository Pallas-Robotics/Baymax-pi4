# OPI4 baseline reconciliation

The OPI4 publishing destination is **Pallas-Robotics/Baymax-pi4**. OPI5 work
continues in [Pallas-Robotics/Baymax](https://github.com/Pallas-Robotics/Baymax),
including its `opi5-fast-all` and `opi5-latency` branches. This candidate does not
change either repository's main or release channel until reviewed.

## History preserved

- OPI4 starting point: `551f80a8fec73f8e19bf5948255152dd1380822d`.
- Shared baseline: `2b8fb72e75cc87643e48119b1a9888798a2e3340`, from
  [Pallas PR #3](https://github.com/Pallas-Robotics/Baymax/pull/3). It already
  contains our OPi4 V1 and SD-card branches; those changes are not reapplied.
- Our remaining work: `6eb21db2551c458f373752b1825746680e924065`, including the
  publishing/channel setup, owner opt-ins, local fall check-ins and working
  protocol from the former NateyKim/Baymax draft PR #1. The merge preserves
  both histories. Historical branch tips are retained separately in the
  destination under `archive/natey/*`. See the [verified branch manifest](migration/NATEY_BRANCHES.json) and [original draft PR record](migration/NATEY_FORK_PR1.md).

## Reconciliation decisions

- Retain Joe's reconnect/backoff, model availability handling, search lookup,
  timing diagnostics, memory-note opt-in and shared-pose duplicate-check-in fix.
- Retain the runtime's single microphone and output stream across network
  reconnects. Device failures stop the capture tasks and close the stream before
  resetting PortAudio and restarting capture. Local Vosk/espeak-ng check-ins
  remain available during network outages when explicitly enabled and prepared.
- Keep Joe's improved language guidance, including accent/script handling and
  English pause words, behind the language-adaptation owner opt-in. Exactly one
  language section is included when enabled, and none of that added section when
  disabled. Gemini's underlying multilingual behavior remains its own.
- Keep CPU pinning in `auto` limited to RK3588. The A733 OPI4 Pro does not receive
  RK3588 pinning, GIL or pinned-speaker defaults. Explicit owner overrides remain
  possible; OPI5 measurements do not establish OPI4 performance.
- Point new OPI4 image/update defaults and contribution instructions at
  Baymax-pi4. Existing cards retain their saved repository, branch and settings;
  this source change does not migrate running devices or rebuild an SD image.
- Preserve both the feature semantic graph and the protocol entry points;
  regenerate derived graph files instead of merging generated conflicts.

## Other contributors' work

James's November 8 v10 robot-rig/live-evaluation changes remain on upstream
`mvp-v10` and are a separate follow-up. Voice recognition (upstream PR #36) and
the v8 core rebuild/cutover (PRs #32/#33) are not imported here. This prevents a
baseline reconciliation from silently changing identity storage or runtime cores.

## Validation and release boundaries

See the draft PR for exact software commands/results. This candidate requires
OPI4 fresh-card and real-device audio/camera/pose, offline speech, reconnect,
device-error recovery, performance and rollback checks. Language adaptation and
offline fall check-ins remain `tested_in_software`, off until owner opt-in.
Software tests and the OPI5 evidence do not certify an OPI4 release. The software
lead still approves merge and promotion.

Do not delete the old fork until destination branch tips and review metadata are
verified. Do not force-push channels or change existing devices as a migration
shortcut. A verified local Git bundle also preserves the pre-migration history.
