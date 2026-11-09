"""Owner opt-ins for experimental features. Importing this module starts nothing."""
import os

FEATURES = {
    "language_adaptation": {
        "setting": "BAYMAX_LANGUAGE_ADAPTATION_ENABLED",
        "stage": "tested_in_software",
    },
    "offline_fall_checkin": {
        "setting": "BAYMAX_OFFLINE_FALL_CHECKIN_ENABLED",
        "stage": "tested_in_software",
    },
}


def enabled(feature):
    """Experimental features require an explicit per-feature owner opt-in."""
    return os.getenv(FEATURES[feature]["setting"], "0") == "1"
