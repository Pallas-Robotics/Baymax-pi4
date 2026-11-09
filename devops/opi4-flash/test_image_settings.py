from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from configure_image import save_private
from image_settings import (DEFAULT_TIMEZONE, REPOSITORY, validate, valid_branch, load, source, supplicant,
                            dietpi_wifi, timezone, valid_timezone)

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location('ember_device_config', HERE / 'payload/ember-device-config.py')
device_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(device_config)


class ImageSettingsTests(unittest.TestCase):
    def setUp(self):
        self.settings = {'branch': 'release', 'wifi': {'ssid': 'IEEE', 'password': 'password'},
                         'gemini_api_key': 'test-key'}

    def test_three_settings_round_trip_and_follow_the_branch(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'private.json'
            save_private(path, self.settings)
            self.assertEqual(load(path), self.settings)
            self.assertEqual(source(load(path)), {'repository': REPOSITORY, 'branch': 'release', 'auto_update': True})

    def test_older_pr_settings_still_load_and_follow_the_pr_ref(self):
        old = {'pr': 20, 'wifi': self.settings['wifi'], 'gemini_api_key': 'test-key'}
        self.assertEqual(validate(old), old)
        self.assertEqual(source(old)['branch'], 'refs/pull/20/head')
        with self.assertRaises(ValueError):                        # one of them, not both
            validate(old | {'branch': 'release'})
        with self.assertRaises(ValueError):                        # and not neither
            validate({'wifi': self.settings['wifi'], 'gemini_api_key': ''})

    def test_branch_rule_matches_the_boards_and_defaults_agree(self):
        for branch in ('release', 'main', 'release/board', 'refs/pull/20/head', 'v1.2_x', '', '-x', 'a..b',
                       'a/', 'a.', 'a.lock', 'a//b', '.hidden', 'a/.b', 'a b', 'a;rm', 7):
            board = True
            try:
                device_config.validate({'branch': branch})
            except ValueError:
                board = False
            self.assertEqual(valid_branch(branch), board, branch)
        self.assertEqual(device_config.DEFAULTS['repository'], REPOSITORY)
        self.assertEqual(device_config.DEFAULTS['branch'], 'deploy')
        self.assertIn(f"DEFAULT_REPOSITORY='{REPOSITORY}'", (HERE / 'payload/ember-update').read_text())
        self.assertEqual(json.loads((HERE / 'settings.example.json').read_text())['branch'], 'deploy')

    def test_optional_access_password_is_validated(self):
        self.assertEqual(validate(self.settings | {'access_password': 'longenough'})['access_password'], 'longenough')
        for bad in ('short', 'has space1', 42):
            with self.assertRaises(ValueError):
                validate(self.settings | {'access_password': bad})

    def test_optional_time_zone_is_validated_and_defaults_to_pacific(self):
        # Check-ins, reminders and the greeting follow the board's clock.
        self.assertEqual(timezone(self.settings), DEFAULT_TIMEZONE)
        self.assertEqual(DEFAULT_TIMEZONE, 'America/Los_Angeles')  # what older images were set to
        for zone in ('America/New_York', 'UTC', 'Etc/GMT+5', 'America/Argentina/Buenos_Aires',
                     'America/Port-au-Prince'):
            self.assertEqual(timezone(validate(self.settings | {'timezone': zone})), zone)
        for bad in ('', 'America/New York', '../../etc/passwd', '/usr/share/zoneinfo/UTC', 'America//X',
                    'America/', 'UTC\nAUTO_SETUP_AUTOMATED=1', 'a' * 65, 7, None):
            self.assertFalse(valid_timezone(bad), bad)
            with self.assertRaises(ValueError):
                validate(self.settings | {'timezone': bad})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'private.json'
            save_private(path, self.settings | {'timezone': 'America/Chicago'})
            self.assertEqual(timezone(load(path)), 'America/Chicago')
        example = validate(json.loads((HERE / 'settings.example.json').read_text()))
        self.assertEqual(timezone(example), DEFAULT_TIMEZONE)

    def test_the_image_gets_the_chosen_time_zone(self):
        inject = (HERE / 'inject_image.py').read_text()
        self.assertIn("'AUTO_SETUP_TIMEZONE': zone,", inject)
        self.assertIn("symlink_to('/usr/share/zoneinfo/' + zone)", inject)
        self.assertIn("write('/etc/timezone', zone + '\\n')", inject)
        self.assertNotIn('America/Los_Angeles', inject)
        validate_image = (HERE / 'validate_image.py').read_text()
        self.assertIn('AUTO_SETUP_TIMEZONE={timezone(settings)}', validate_image)
        self.assertIn("readlink(root / 'etc/localtime')", validate_image)

    def test_wpa_derivation_matches_known_vector(self):
        text = supplicant(self.settings['wifi'])
        self.assertIn('ssid=49454545', text)
        self.assertIn('psk=f42c6fc52df0ebef9ebb4b90b38a5f902e83fe1b135a70e23aed762e9710a12e', text)
        self.assertNotIn('password', text)

    def test_open_network_has_no_psk(self):
        text = supplicant({'ssid': 'Apartment', 'password': ''})
        self.assertIn('key_mgmt=NONE', text)
        self.assertNotIn('psk=', text)

    def test_shell_metacharacters_are_quoted_and_missing_fields_rejected(self):
        text = dietpi_wifi("aWIFI_SSID[0]=''\naWIFI_KEY[0]=''\n", {'ssid': "O'Brien $(echo test)", 'password': 'pass$word'})
        self.assertIn("'\"'\"'", text)
        self.assertIn("'pass$word'", text)
        with self.assertRaises(ValueError):
            dietpi_wifi('', self.settings['wifi'])

    def test_bad_values_do_not_replace_valid_settings(self):
        for invalid in (True, -1):
            with self.assertRaises(ValueError):
                validate({'pr': invalid, 'wifi': self.settings['wifi'], 'gemini_api_key': ''})
        for field, invalid in (('branch', 'bad branch'), ('branch', '../up'), ('branch', 20),
                               ('gemini_api_key', 'key\ncommand')):
            data = deepcopy(self.settings)
            data[field] = invalid
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'settings.json'
                save_private(path, self.settings)
                with self.assertRaises(ValueError):
                    save_private(path, data)
                self.assertEqual(load(path), self.settings)
        for wifi in ({'ssid': 'x' * 33, 'password': ''}, {'ssid': 'name\nother', 'password': ''},
                     {'ssid': 'ok', 'password': 'short'}):
            with self.assertRaises(ValueError):
                validate(self.settings | {'wifi': wifi})


if __name__ == '__main__':
    unittest.main()
