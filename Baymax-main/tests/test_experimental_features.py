"""Experimental testing stages do not grant implicit activation or release approval."""
import os
import unittest
from unittest.mock import patch

from features import experimental, persona
from features.toolkits import offline_fall


class ExperimentalFeatureTests(unittest.TestCase):
    def test_every_experiment_defaults_off_and_requires_an_explicit_one(self):
        for feature, details in experimental.FEATURES.items():
            with self.subTest(feature=feature), patch.dict(os.environ, {}, clear=True):
                self.assertFalse(experimental.enabled(feature))
                for value in ("0", "false", "true", "yes", "", "2"):
                    os.environ[details["setting"]] = value
                    self.assertFalse(experimental.enabled(feature))
                os.environ[details["setting"]] = "1"
                self.assertTrue(experimental.enabled(feature))

    def test_language_guidance_is_owner_opt_in_and_preserves_the_base_persona(self):
        config = {"system_instruction": persona.UPSTREAM_MARKER, "other": "unchanged"}
        with patch.dict(os.environ, {"BAYMAX_LANGUAGE_ADAPTATION_ENABLED": "0"}):
            default = persona.apply(config)
        with patch.dict(os.environ, {"BAYMAX_LANGUAGE_ADAPTATION_ENABLED": "1"}):
            opted_in = persona.apply(config)
        self.assertEqual(default["system_instruction"], persona.PERSONA)
        self.assertEqual(opted_in["system_instruction"], persona.PERSONA + "\n" + persona.LANGUAGE_GUIDANCE)
        self.assertEqual(opted_in["other"], "unchanged")
        self.assertEqual(config["system_instruction"], persona.UPSTREAM_MARKER)
        self.assertNotIn("[LANGUAGE]", default["system_instruction"])
        self.assertEqual(opted_in["system_instruction"].count("[LANGUAGE]"), 1)
        self.assertIn("not by their accent", opted_in["system_instruction"])
        self.assertIn('"Hey Ember"', opted_in["system_instruction"])

    def test_fall_opt_in_is_independent_of_language_opt_in(self):
        with patch.dict(os.environ, {"BAYMAX_LANGUAGE_ADAPTATION_ENABLED": "1",
                                     "BAYMAX_OFFLINE_FALL_CHECKIN_ENABLED": "0"}):
            self.assertFalse(offline_fall.enabled())
        with patch.dict(os.environ, {"BAYMAX_LANGUAGE_ADAPTATION_ENABLED": "0",
                                     "BAYMAX_OFFLINE_FALL_CHECKIN_ENABLED": "1"}):
            self.assertTrue(offline_fall.enabled())
