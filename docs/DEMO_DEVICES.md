# OPI4 target and development hosts

This fork targets Orange Pi 4 Pro (Allwinner A733), native Linux ARM64/Python 3.12
and CPU pose processing. Desktop platforms serve development/offline checks;
their results do not establish OPI4 hardware readiness.

OPI5 and LattePanda work live in separate upstream repositories/branches. Their
drivers, scheduling policies, tuning and hardware evidence are not this fork's
active platform configuration. Shared fixes are reconciled individually.

See [OPI4 setup](../Baymax-main/ORANGE_PI_SETUP.md),
[reconciliation](OPI4_RECONCILIATION.md) and the
[testing protocol](../Baymax-main/TESTING_PROTOCOL.md). The 4 Pro image is board
specific; fresh-card boot and actual audio/camera/pose checks remain pending.
