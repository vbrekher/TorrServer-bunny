import importlib.util
import pathlib
import time
import unittest
import tempfile
from unittest.mock import patch
from types import SimpleNamespace

CLI = pathlib.Path(__file__).resolve().parents[1] / 'bunny' / 'cli.py'
spec = importlib.util.spec_from_file_location('bunny_cli', CLI)
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


class CLIConfigTests(unittest.TestCase):
    def test_regions(self):
        self.assertEqual(cli.normalize_regions({'items': [{'id': 'DE', 'name': 'Germany'}, {'regionId': 'NL', 'displayName':'Netherlands'}]}), [('DE', 'Germany'), ('NL', 'Netherlands')])

    def test_payload_one_region_and_https(self):
        x = cli.build_payload('DE','lampa','random_PW','secret', image_registry_id='123')
        self.assertEqual(x['autoScaling'], {'min': 1, 'max': 1})
        self.assertEqual({k: x['containerTemplates'][0][k] for k in ('imageName', 'imageNamespace', 'imageTag', 'imagePullPolicy', 'imageRegistryId')}, {'imageName': 'torrserver-bunny', 'imageNamespace': 'vbrekher', 'imageTag': 'main', 'imagePullPolicy': 'always', 'imageRegistryId': '123'})
        self.assertEqual(x['regionSettings']['requiredRegionIds'], ['DE'])
        self.assertEqual(x['containerTemplates'][0]['endpoints'][0]['cdn']['portMappings'][0]['containerPort'], 8080)
        self.assertEqual(x['volumes'][0]['size'], 1)
        self.assertEqual(len(x['containerTemplates'][0]['endpoints']), 1)
        self.assertEqual(len(cli.build_payload('DE', 'lampa', 'pw', 'secret', public_peers=True, image_registry_id='123')['containerTemplates'][0]['endpoints']), 2)

    def test_create_payload_matches_official_cli_required_shape(self):
        # Official BunnyWay/cli packages/config/src/convert.ts uses precisely
        # allowedRegionIds + requiredRegionIds and CDN mapping without protocols.
        p = cli.build_payload('AMS', 'letin', 'pwd', 'token', image_registry_id='91')
        self.assertEqual(set(p), {'name', 'runtimeType', 'autoScaling', 'regionSettings',
                                  'containerTemplates', 'volumes'})
        self.assertEqual(p['regionSettings'], {
            'allowedRegionIds': ['AMS'], 'requiredRegionIds': ['AMS']})
        c = p['containerTemplates'][0]
        self.assertEqual(c['image'], 'ghcr.io/vbrekher/torrserver-bunny:main')
        self.assertEqual(c['imageRegistryId'], '91')
        self.assertEqual(c['imagePullPolicy'], 'always')
        self.assertEqual(c['endpoints'], [{
            'displayName': 'torrserver-https',
            'cdn': {'isSslEnabled': True, 'portMappings': [{'containerPort': 8080, 'exposedPort': 80}]}
        }])
        self.assertEqual(p['volumes'], [{'name': 'config', 'size': 1}])

    def test_rejects_symbolic_registry_alias_before_paid_app(self):
        with self.assertRaisesRegex(cli.DeploymentError, 'not the alias github'):
            cli.build_payload('AMS', 'letin', 'pw', 'token', image_registry_id='github')
        data = {'items': [{'id': 'github', 'hostName': 'ghcr.io'},
                          {'id': 812, 'hostName': 'ghcr.io'}]}
        self.assertEqual(cli.registry_ids(data), ['812'])
        with patch.object(cli, 'request', return_value={'digest': 'sha256:' + 'b'*64}) as req:
            self.assertEqual(cli.ensure_registry('key', data), '812')
            req.assert_called_once()
            self.assertEqual(req.call_args.args[3]['registryId'], '812')

    def test_public_ghcr_reference_validation(self):
        with self.assertRaises(cli.DeploymentError):
            cli.split_image('ghcr.io/vbrekher/torrserver-bunny')
        with self.assertRaises(cli.DeploymentError):
            cli.split_image('https://evil.net/bad:latest')
        with self.assertRaises(cli.DeploymentError):
            cli.build_payload('DE', 'lampa', 'pwd', 'token')

    def test_multiple_registries_are_not_deleted(self):
        data = {'items': [{'id': 1, 'hostName': 'docker.io'}, {'id': 91, 'hostName': 'ghcr.io'},
                          {'id': 92, 'hostName': 'https://ghcr.io/'}, {'id': 91, 'hostName': 'ghcr.io'}]}
        self.assertEqual(cli.registry_ids(data), ['91', '92'])
        lookups = []
        def remote(method, path, key, payload):
            self.assertEqual((method, path), ('POST', '/mc/registries/digest'))
            lookups.append(payload['registryId'])
            if payload['registryId'] == '91':
                raise cli.DeploymentError('Not visible in this registry')
            return {'digest': 'sha256:' + 'a'*64}
        with patch.object(cli, 'request', side_effect=remote) as req:
            self.assertEqual(cli.ensure_registry('secret', data), '92')
            self.assertEqual(lookups, ['91', '92'])
            self.assertEqual(req.call_count, 2)

    def test_numeric_existing_ghcr_preferred_no_registry_mutation(self):
        data = {'items': [{'id': 91, 'hostName': 'ghcr.io'}, {'id': 92, 'hostName': 'ghcr.io'}]}
        with patch.object(cli, 'request', return_value={'digest': 'sha256:'+'b'*64}) as req:
            self.assertEqual(cli.ensure_registry('secret', data), '91')
            self.assertEqual(req.call_count, 1)
            self.assertEqual(req.call_args.args[1], '/mc/registries/digest')

    def test_registry_fail_closed_before_app_post(self):
        with patch.object(cli, 'request', side_effect=cli.DeploymentError('Denied')) as req:
            with self.assertRaises(cli.DeploymentError):
                cli.ensure_registry('secret', {'items': [{'id': 91, 'hostName': 'ghcr.io'}]})
            self.assertEqual(req.call_count, 1)

    def test_rejects_malformed_digest(self):
        with patch.object(cli, 'request', return_value={'digest': 'not a sha256'}):
            with self.assertRaises(cli.DeploymentError):
                cli.ensure_registry('secret', {'items': [{'id': 91, 'hostName': 'ghcr.io'}]})

    def test_existing_app_refuses_duplication(self):
        with patch.object(cli, 'request', return_value={'items': [{'name': 'torrserver-bunny', 'id': 'existing'}]}):
            with self.assertRaises(cli.DeploymentError):
                cli.check_no_duplicate_app('secret')

    def test_setup_validates_request_before_paid_creation(self):
        requests = []
        def fake_request(method, path, key=None, payload=None, **kwargs):
            requests.append((method, path, payload))
            if method == 'GET' and path == '/mc/apps?limit=100': return {'items': []}
            if method == 'GET' and path == '/mc/registries': return {'items': [{'id': 7, 'hostName': 'ghcr.io'}, {'id': 8, 'hostName': 'ghcr.io'}]}
            if method == 'POST' and path == '/mc/registries/digest': return {'digest': 'sha256:'+'c'*64}
            if method == 'GET' and path == '/mc/regions': return {'items': [{'id': 'DE', 'name': 'Germany'}]}
            if method == 'POST' and path == '/mc/apps': return {'id': 'app-123'}
            if method == 'GET' and path == '/mc/apps/app-123': return {'containerTemplates': [{'name': 'torrserver', 'id': 'ct-123'}]}
            if method == 'POST' and path.endswith('/containers/ct-123/endpoints'): return {'id': 'anycast-123'}
            if method == 'POST' and path.endswith('/deploy'): return {}
            if method == 'GET' and path.endswith('/endpoints'): return {'items': [{'hostname': 'mc-example.bunny.run'}]}
            raise AssertionError((method, path))
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(cli, 'CONFIG', pathlib.Path(tmp) / 'config.json'), \
                 patch.object(cli, 'ask', side_effect=['secret', '1', 'letin', 'y', 'CREATE']), \
                 patch.object(cli, 'request', side_effect=fake_request):
                cli.setup(SimpleNamespace(image=cli.IMAGE, no_deploy=False))
                app_posts = [payload for method, path, payload in requests if method == 'POST' and path == '/mc/apps']
                self.assertEqual(len(app_posts), 1)
                self.assertEqual(app_posts[0]['containerTemplates'][0]['imageRegistryId'], '7')
                self.assertEqual(len(app_posts[0]['containerTemplates'][0]['endpoints']), 1)
                self.assertEqual(len([p for m,p,_ in requests if m=='POST' and p.endswith('/containers/ct-123/endpoints')]), 1)
                self.assertTrue(cli.load_config()['public_peers'])


    def test_pagination_detects_existing_app_on_later_page(self):
        def fake(method, path, key):
            if path == '/mc/apps?limit=100':
                return {'items': [{'name':'unrelated'}], 'cursor': 'page-2'}
            if path == '/mc/apps?limit=100&nextCursor=page-2':
                return {'items': [{'name': 'torrserver-bunny', 'id': 'existing'}]}
            raise AssertionError(path)
        with patch.object(cli, 'request', side_effect=fake):
            with self.assertRaisesRegex(cli.DeploymentError, 'existing'):
                cli.check_no_duplicate_app('secret')

    def test_http500_zero_apps_never_retries_creation(self):
        calls = []
        def fake(method, path, key, payload=None):
            calls.append((method, path))
            if method == 'POST':
                raise cli.DeploymentError('Bunny/remote HTTP 500: Internal Server Error')
            if method == 'GET' and path == '/mc/apps?limit=100':
                return {'items': []}
            raise AssertionError(path)
        with patch.object(cli, 'request', side_effect=fake):
            with self.assertRaisesRegex(cli.DeploymentError, 'no second POST'):
                cli.create_app_safely('secret', {'name': 'torrserver-bunny'}, 'DE', cli.IMAGE, '91')
        self.assertEqual([x for x in calls if x[0] == 'POST'], [('POST', '/mc/apps')])

    def test_http500_recovers_exact_new_app(self):
        def fake(method, path, key, payload=None):
            if method == 'POST' and path == '/mc/apps':
                raise cli.DeploymentError('Bunny/remote HTTP 500: Internal Server Error')
            if method == 'GET' and path == '/mc/apps?limit=100':
                return {'items': [{'name': 'torrserver-bunny', 'id': 'app-new'}]}
            if method == 'GET' and path == '/mc/apps/app-new':
                return {'name': 'torrserver-bunny', 'regionSettings': {'requiredRegionIds': ['DE']},
                        'containerTemplates': [{'name': 'torrserver', 'imageName': 'torrserver-bunny',
                                                'imageNamespace': 'vbrekher', 'imageTag': 'main',
                                                'imageRegistryId': '91'}]}
            raise AssertionError(path)
        with patch.object(cli, 'request', side_effect=fake):
            self.assertEqual(cli.create_app_safely('secret', {'name': 'torrserver-bunny'}, 'DE', cli.IMAGE, '91'), 'app-new')

    def test_http500_does_not_adopt_mismatched_app(self):
        def fake(method, path, key, payload=None):
            if method == 'POST':
                raise cli.DeploymentError('Bunny/remote HTTP 500: Internal Server Error')
            if path == '/mc/apps?limit=100':
                return {'items': [{'name': 'torrserver-bunny', 'id': 'app-wrong'}]}
            if path == '/mc/apps/app-wrong':
                return {'name': 'torrserver-bunny', 'regionSettings': {'requiredRegionIds': ['NL']},
                        'containerTemplates': [{'name': 'other'}]}
            raise AssertionError(path)
        with patch.object(cli, 'request', side_effect=fake):
            with self.assertRaisesRegex(cli.DeploymentError, 'could not be verified'):
                cli.create_app_safely('secret', {'name': 'torrserver-bunny'}, 'DE', cli.IMAGE, '91')

    def test_enable_peers_is_idempotent(self):
        calls = []
        def fake(method, path, key, payload=None):
            calls.append((method, path))
            if path.endswith('/endpoints') and method == 'GET':
                return {'items': [{'displayName': 'torrent-peers'}]}
            raise AssertionError(path)
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(cli, 'CONFIG', pathlib.Path(tmp) / 'config.json'), patch.object(cli, 'request', side_effect=fake):
                c = {'api_key': 'secret', 'app_id': 'app-123', 'public_peers': False}
                cli.enable_peer_endpoint(c)
                self.assertTrue(cli.load_config()['public_peers'])
                self.assertFalse(any(x[0]=='POST' for x in calls))

    def test_doctor_read_only(self):
        calls=[]
        def fake(method, path, key):
            calls.append(method)
            return {'items': []}
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(cli, 'CONFIG', pathlib.Path(tmp) / 'missing.json'), \
                 patch.object(cli, 'ask', return_value='secret'), patch.object(cli, 'request', side_effect=fake):
                cli.doctor()
        self.assertEqual(calls, ['GET', 'GET', 'GET'])  # apps + registries + limits, all read-only

    def test_safe_url_only(self):
        self.assertEqual(cli.find_https_url({'endpoints':[{'cdn': {'hostname': 'mc-example.bunny.run', 'isSslEnabled': True}}]}), 'https://mc-example.bunny.run')
        self.assertIsNone(cli.find_https_url({'id': 'id-1234', 'endpoints': []}))
        self.assertEqual(cli.find_https_url({'items': [{'type':'cdn', 'isSslEnabled': True, 'publicHost': 'mc-live.bunny.run'}]}), 'https://mc-live.bunny.run')
        self.assertEqual(cli.find_https_url({'displayEndpoint': {'address': 'mc-secondary.bunny.run', 'type': 'CDN'}}), 'https://mc-secondary.bunny.run')


    def test_never_select_paid_anycast_ip_as_lampa_url(self):
        data = {'items': [
            {'type': 'anycast', 'isSslEnabled': False, 'publicHost': '109.224.231.152:32000',
             'displayName': 'torrent-peers'},
            {'type': 'cdn', 'isSslEnabled': True, 'publicHost': 'mc-real.bunny.run',
             'displayName': 'torrserver-https'}
        ]}
        self.assertEqual(cli.find_https_url(data), 'https://mc-real.bunny.run')
        self.assertIsNone(cli.find_https_url({'items': [data['items'][0]]}))
        self.assertIsNone(cli.canonical_https_endpoint('https://109.224.231.152:32000'))
        self.assertIsNone(cli.canonical_https_endpoint('https://example.com:32000'))
        self.assertIsNone(cli.canonical_https_endpoint('http://mc-real.bunny.run'))
        self.assertEqual(cli.canonical_https_endpoint('mc-real.bunny.run'), 'https://mc-real.bunny.run')

    def test_app_display_endpoint_anycast_ignored(self):
        app = {'displayEndpoint': {'address': '109.224.231.152:32000', 'type': 'anycast'},
               'containerTemplates': [{'endpoints': [
                   {'type': 'cdn', 'publicHost': 'mc-cdn.bunny.run', 'isSslEnabled': True}
               ]}]}
        self.assertEqual(cli.find_https_url(app), 'https://mc-cdn.bunny.run')
        self.assertIsNone(cli.find_https_url({'displayEndpoint': app['displayEndpoint']}))

    def test_status_repairs_saved_anycast_url_and_masks_password(self):
        with tempfile.TemporaryDirectory() as tmp:
            c = {'api_key': 'secret', 'app_id': 'HznUbyXuN3o1dpA', 'region': 'AMS',
                 'username': 'letin', 'password': 'DO_NOT_PRINT',
                 'url': 'https://109.224.231.152:32000'}
            def fake(method, path, key, payload=None):
                if path == '/mc/apps/HznUbyXuN3o1dpA':
                    return {'status': 'running', 'containerTemplates': [
                        {'endpoints': [{'type': 'cdn', 'isSslEnabled': True,
                                        'publicHost': 'mc-real.bunny.run'}]}]}
                if path == '/mc/apps/HznUbyXuN3o1dpA/endpoints':
                    return {'items': [
                        {'type': 'anycast', 'publicHost': '109.224.231.152:32000',
                         'isSslEnabled': False},
                        {'type': 'cdn', 'publicHost': 'mc-real.bunny.run',
                         'isSslEnabled': True}]}
                raise AssertionError(path)
            import io
            from contextlib import redirect_stdout
            with patch.object(cli, 'CONFIG', pathlib.Path(tmp) / 'config.json'):
                cli.save_config(c)
                with patch.object(cli, 'request', side_effect=fake):
                    output = io.StringIO()
                    with redirect_stdout(output):
                        cli.status()
                    self.assertEqual(cli.load_config()['url'], 'https://mc-real.bunny.run')
                    self.assertNotIn('DO_NOT_PRINT', output.getvalue())
                    self.assertIn('https://mc-real.bunny.run', output.getvalue())
                    output2 = io.StringIO()
                    with redirect_stdout(output2):
                        cli.status(show_credentials=True)
                    self.assertIn('DO_NOT_PRINT', output2.getvalue())

    def test_status_does_not_reuse_wrong_ip_if_cdn_not_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            c = {'api_key': 'secret', 'app_id': 'id', 'region': 'AMS', 'username': 'letin',
                 'password': 'secretpw', 'url': 'https://109.224.231.152:32000'}
            import io
            from contextlib import redirect_stdout
            with patch.object(cli, 'CONFIG', pathlib.Path(tmp) / 'config.json'):
                cli.save_config(c)
                with patch.object(cli, 'request', return_value={'status': 'deploying'}):
                    with redirect_stdout(io.StringIO()): cli.status()
                self.assertIsNone(cli.load_config()['url'])

    def test_activity_command_is_read_only_and_reports_tracking(self):
        import io
        from contextlib import redirect_stdout
        with patch.object(cli, 'activity_snapshot', return_value=(
                {'active_streams': 0, 'last_media_unix': 1000, 'media_bytes': 20480}, 4601)):
            stream = io.StringIO()
            with redirect_stdout(stream):
                cli.activity_status()
            result = stream.getvalue()
            self.assertIn('Tracked media bytes since container startup: 20480', result)
            self.assertIn('Minutes since last tracked media: 60', result)
            self.assertIn('Eligible to stop after 60 idle minutes: yes', result)
            self.assertIn('READ_ONLY', result)

    def test_activity_warning_if_no_media_was_tracked(self):
        import io
        from contextlib import redirect_stdout
        with patch.object(cli, 'activity_snapshot', return_value=(
                {'active_streams': 0, 'last_media_unix': 1000, 'media_bytes': 0}, 1010)):
            stream = io.StringIO()
            with redirect_stdout(stream):
                cli.activity_status()
            self.assertIn('No media bytes tracked', stream.getvalue())
            self.assertIn('Minutes since gateway startup (no video tracked yet)', stream.getvalue())
            self.assertIn('Eligible to stop after 60 idle minutes: no', stream.getvalue())

    def test_activity_shows_route_class_diagnostics_without_any_urls(self):
        import io
        from contextlib import redirect_stdout
        state = {'active_streams': 0, 'last_media_unix': 1000, 'media_bytes': 0,
                 'proxy_requests': 7, 'media_requests': 0, 'other_requests': 7,
                 'other_response_bytes': 8912, 'unclassified_media_bytes': 3000}
        with patch.object(cli, 'activity_snapshot', return_value=(state, 1010)):
            output = io.StringIO()
            with redirect_stdout(output):
                cli.activity_status()
            result = output.getvalue()
            self.assertIn('Gateway proxied requests since startup: 7', result)
            self.assertIn('Recognized stream requests: 0', result)
            self.assertIn('Video-like bytes on unrecognized paths: 3000', result)
            self.assertIn('HTTP traffic reached the gateway but no recognized', result)
            self.assertIn('Automatic shutdown is blocked', result)
            self.assertNotIn('http://', result)

    def test_idle_check_refuses_unclassified_video_in_both_passes(self):
        import io
        from contextlib import redirect_stdout
        base = {'active_streams': 0, 'last_media_unix': 100,
                'media_bytes': 20480, 'unclassified_media_bytes': 100}
        cfg = {'api_key': 'hidden', 'app_id': 'app', 'url': 'https://example.bunny.run',
               'watchdog_token': 'hidden'}
        with patch.object(cli, 'load_config', return_value=cfg), \
             patch.object(cli, 'get_activity', return_value=base), \
             patch.object(cli.time, 'time', return_value=5000), \
             patch.object(cli, 'request') as remote, \
             redirect_stdout(io.StringIO()) as output:
            cli.idle_check(SimpleNamespace(remote=False, minutes=60, no_pause=True))
            self.assertIn('SAFE_NO_STOP', output.getvalue())
            remote.assert_not_called()

    def test_watchdog_enrollment_refuses_unclassified_video(self):
        cfg = {'url': 'https://example.bunny.run'}
        with patch.object(cli, 'load_config', return_value=cfg), \
             patch.object(cli, 'activity_snapshot', return_value=(
                 {'active_streams': 0, 'last_media_unix': 100,
                  'media_bytes': 10000, 'unclassified_media_bytes': 500}, 5000)):
            with self.assertRaisesRegex(cli.DeploymentError, 'Unclassified media response'):
                cli.github_watchdog(SimpleNamespace(repo='vbrekher/TorrServer-bunny'))

    def test_idle_check_fails_safe_when_no_video_bytes(self):
        import io
        from contextlib import redirect_stdout
        state = {'active_streams': 0, 'last_media_unix': 100, 'media_bytes': 0}
        cfg = {'api_key': 'hidden', 'app_id': 'app', 'url': 'https://example.bunny.run',
               'watchdog_token': 'hidden'}
        with patch.object(cli, 'load_config', return_value=cfg), \
             patch.object(cli, 'get_activity', return_value=state), \
             patch.object(cli.time, 'time', return_value=5000), \
             patch.object(cli, 'request') as remote, \
             redirect_stdout(io.StringIO()) as output:
            cli.idle_check(SimpleNamespace(remote=False, minutes=60, no_pause=True))
            self.assertIn('SAFE_NO_STOP', output.getvalue())
            remote.assert_not_called()

    def test_idle_check_undeploys_only_after_two_valid_idle_reads(self):
        import io
        from contextlib import redirect_stdout
        cfg = {'api_key': 'hidden', 'app_id': 'app', 'url': 'https://example.bunny.run',
               'watchdog_token': 'hidden'}
        old_state = {'active_streams': 0, 'last_media_unix': 100, 'media_bytes': 100000}
        with patch.object(cli, 'load_config', return_value=cfg), \
             patch.object(cli, 'get_activity', return_value=old_state) as tracked, \
             patch.object(cli.time, 'time', return_value=5000), \
             patch.object(cli.time, 'sleep'), \
             patch.object(cli, 'request', return_value=None) as remote, \
             redirect_stdout(io.StringIO()):
            cli.idle_check(SimpleNamespace(remote=False, minutes=60, no_pause=False))
            self.assertEqual(tracked.call_count, 2)
            remote.assert_called_once_with('POST', '/mc/apps/app/undeploy', 'hidden')

    def test_idle_check_refuses_if_second_read_detects_active_stream(self):
        import io
        from contextlib import redirect_stdout
        cfg = {'api_key': 'hidden', 'app_id': 'app', 'url': 'https://example.bunny.run',
               'watchdog_token': 'hidden'}
        old_state = {'active_streams': 0, 'last_media_unix': 100, 'media_bytes': 100000}
        new_state = {'active_streams': 1, 'last_media_unix': 4990, 'media_bytes': 100100}
        with patch.object(cli, 'load_config', return_value=cfg), \
             patch.object(cli, 'get_activity', side_effect=[old_state,new_state]), \
             patch.object(cli.time, 'time', return_value=5000), \
             patch.object(cli.time, 'sleep'), \
             patch.object(cli, 'request') as remote, \
             redirect_stdout(io.StringIO()):
            cli.idle_check(SimpleNamespace(remote=False, minutes=60, no_pause=False))
            remote.assert_not_called()

    def test_github_watchdog_blocks_unobserved_playback(self):
        cfg = {'url': 'https://example.bunny.run'}
        with patch.object(cli, 'load_config', return_value=cfg), \
             patch.object(cli, 'activity_snapshot', return_value=(
                 {'active_streams':0, 'last_media_unix': 100, 'media_bytes':0}, 2000)):
            with self.assertRaisesRegex(cli.DeploymentError, 'No media bytes tracked'):
                cli.github_watchdog(SimpleNamespace(repo='vbrekher/TorrServer-bunny'))

    def test_idle_active_prevents_shutdown(self):
        now = time.time()
        self.assertFalse(cli.can_stop({'active_streams':1, 'last_media_unix': now-86400}, now, 3600))
        self.assertFalse(cli.can_stop({'active_streams':0, 'last_media_unix': now-3599}, now, 3600))
        self.assertTrue(cli.can_stop({'active_streams':0, 'last_media_unix': now-3601}, now, 3600))
        with self.assertRaises(cli.DeploymentError):
            cli.can_stop({'active_streams':0}, now, 3600)


if __name__ == '__main__': unittest.main()
