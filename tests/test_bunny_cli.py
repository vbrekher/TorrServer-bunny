import importlib.util
import pathlib
import time
import unittest

CLI = pathlib.Path(__file__).resolve().parents[1] / 'bunny' / 'cli.py'
spec = importlib.util.spec_from_file_location('bunny_cli', CLI)
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


class CLIConfigTests(unittest.TestCase):
    def test_regions(self):
        self.assertEqual(cli.normalize_regions({'items': [{'id': 'DE', 'name': 'Germany'}, {'regionId': 'NL', 'displayName':'Netherlands'}]}), [('DE', 'Germany'), ('NL', 'Netherlands')])

    def test_payload_one_region_and_https(self):
        x = cli.build_payload('DE','lampa','random_PW','secret')
        self.assertEqual(x['autoScaling'], {'min': 1, 'max': 1})
        self.assertEqual(x['regionSettings']['requiredRegionIds'], ['DE'])
        self.assertEqual(x['containerTemplates'][0]['endpoints'][0]['cdn']['portMappings'][0]['containerPort'], 8080)
        self.assertEqual(x['volumes'][0]['size'], 1)
        self.assertEqual(len(x['containerTemplates'][0]['endpoints']), 1)
        self.assertEqual(len(cli.build_payload('DE', 'lampa', 'pw', 'secret', public_peers=True)['containerTemplates'][0]['endpoints']), 2)

    def test_safe_url_only(self):
        self.assertEqual(cli.find_https_url({'endpoints':[{'cdn': {'hostname': 'mc-example.bunny.run'}}]}), 'https://mc-example.bunny.run')
        self.assertIsNone(cli.find_https_url({'id': 'id-1234', 'endpoints': []}))

    def test_idle_active_prevents_shutdown(self):
        now = time.time()
        self.assertFalse(cli.can_stop({'active_streams':1, 'last_media_unix': now-86400}, now, 3600))
        self.assertFalse(cli.can_stop({'active_streams':0, 'last_media_unix': now-3599}, now, 3600))
        self.assertTrue(cli.can_stop({'active_streams':0, 'last_media_unix': now-3601}, now, 3600))
        with self.assertRaises(cli.DeploymentError):
            cli.can_stop({'active_streams':0}, now, 3600)


if __name__ == '__main__': unittest.main()
