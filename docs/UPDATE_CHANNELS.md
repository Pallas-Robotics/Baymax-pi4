# Ember publishing authority and channels

The authoritative publishing repository for Ember is
**https://github.com/Pallas-Robotics/Baymax-pi4**. It remains a GitHub fork, but Ember releases
and channel updates are published here. Upstream repositories remain sources for
reviewed contributions. Devices fetch one configured repository/branch; they do
not merge forks automatically.

| Channel branch | Intended readiness |
|---|---|
| `experimental` | Unvalidated development for bench use only |
| `needssoftwaretest` | Development candidate awaiting software validation |
| `needssimtest` | Software-tested candidate awaiting chamber video/audio replay |
| `needshardwaretest` | Chamber-tested candidate awaiting controlled physical trials |
| `deploy` | Version approved for ordinary deployment |

Historical channel pointers are preserved at their original commits under
`archive/natey/*`; these archive refs are not deployment channels. Operational
channel creation/configuration in Baymax-pi4 is a separate release-maintainer
step before using the new image defaults.
The reconciled candidate is a draft PR, not a channel promotion. `main` and
`release` keep the destination baseline until reviewed. Existing devices retain
their configured repository and branch; no active robot is switched by this PR.


## CI behavior

Every channel push runs the existing four-platform offline gate (Linux ARM64,
Linux desktop, Windows and macOS) and a robot-image build check. Path filters are
removed so documentation, deployment and configuration changes also trigger CI.
Pull requests still run these checks. The inherited container image targets
Linux AMD64; the separate ARM64 offline job checks the Orange Pi dependency
profile. Image checks on channel branches do not publish image tags or perform
container promotion. Existing main publishing and manual Promote release remain
separate from Git source channels.

Channels describe intended validation readiness; branch names do not enforce it.
Before promoting a revision, review its required automated results and record
chamber/physical evidence against the exact commit, board, OS, peripherals and
models. Preserve known failures. A behavior-changing revision needs new relevant
evidence. Software-lead approval remains required for deployment. Set GitHub
required status checks/review protection separately if branch enforcement is
needed; simply adding workflow triggers does not add branch protection.

## Owner selection

Use **Ember Device Settings → Git repository, branch and automatic updates**.
New SD configurations default to `https://github.com/Pallas-Robotics/Baymax-pi4.git` and
`deploy`. Owner settings in `~/.config/ember/device.json` persist across updates.
Existing devices keep their saved repository/channel; existing images must be
rebuilt or deliberately migrated to adopt these new defaults.

```bash
/opt/ember-python/python/bin/python3.12 /opt/ember-provision/ember-device-config.py save \
  --repository https://github.com/Pallas-Robotics/Baymax-pi4.git \
  --branch deploy --auto-update true
```

Saving chooses the source; the normal update action or next boot fetches it.
Automatic checks occur at the updater's existing boot/manual schedule, not on
every GitHub push immediately. Owners can turn auto-update off. Existing `main`,
`release` and `opi4-chat-timing` branches are retained; the legacy git-checkout
updater still defaults to `release` unless its owner chooses another branch.

The SD updater checks installation/imports and switches release paths. It does
not establish chamber/hardware readiness or guarantee every failure rolls back.
Validate update, health-failure, power-loss and recovery behavior for each board
before fleet rollout. Feature test status and feature opt-in are separate from
the owner's update channel.

Experimental features require separate owner opt-ins; see [feature stages](../Baymax-main/features/experimental/README.md).

Approved deploy fixes flow into testing branches through reviewed sync PRs. Never merge channels on the robot. See [working protocol](WORKING_PROTOCOL.md) and [rollout checklist](ROLLOUT_TODO.md).
