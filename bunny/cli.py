#!/usr/bin/env python3
"""TorrServer Bunny: optional-dependency-free Magic Containers deployment/controller.

Uses documented Bunny /mc endpoints. No API keys leave the user's machine except to
Bunny's API and, only if opted in, their own GitHub Actions repository secrets.
"""
import argparse
import base64
import getpass
import json
import os
import pathlib
import re
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

API = 'https://api.bunny.net'
IMAGE = 'ghcr.io/vbrekher/torrserver-bunny:main'
CONFIG = pathlib.Path.home() / '.config' / 'torrserver-bunny' / 'config.json'
CLI_BUILD = '2026-11-02-registry-digest-verified'
USER_AGENT = 'TorrServer-bunny/0.2 (+https://github.com/vbrekher/TorrServer-bunny)'


class DeploymentError(Exception):
    pass


def ask(label, default=None, hidden=False):
    suffix = f' [{default}]' if default else ''
    response = (getpass.getpass(f'{label}{suffix}: ') if hidden else input(f'{label}{suffix}: ')).strip()
    return response or default


def request(method, path, key=None, payload=None, base=API, extra_headers=None):
    url = path if path.startswith('https://') else base + path
    if not url.startswith('https://'):
        raise DeploymentError('Only HTTPS API requests are permitted')
    headers = {'User-Agent': USER_AGENT, 'Accept': 'application/json', **(extra_headers or {})}
    if key:
        headers['AccessKey'] = key
    data = None
    if payload is not None:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(payload).encode('utf-8')
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers, method=method, data=data), timeout=25) as response:
            body = response.read(512 * 1024)
            if not body:
                return None
            try:
                return json.loads(body)
            except ValueError:
                return body.decode('utf-8', 'replace')
    except urllib.error.HTTPError as exc:
        # Do not print original URL or request body (could contain secrets).
        safe = exc.read(1200).decode('utf-8', 'replace')
        raise DeploymentError(f'Bunny/remote HTTP {exc.code}: {safe}') from None
    except urllib.error.URLError as exc:
        raise DeploymentError(f'Network request failed: {exc.reason}') from None


def load_config():
    if not CONFIG.exists():
        raise DeploymentError('Not configured. Run: torrserver-bunny setup')
    if CONFIG.stat().st_mode & 0o077:
        raise DeploymentError(f'Insecure configuration permissions: chmod 600 {CONFIG}')
    return json.loads(CONFIG.read_text('utf-8'))


def save_config(c):
    CONFIG.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(CONFIG.parent, 0o700)
    fd = os.open(str(CONFIG), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(c, f, indent=2)
        f.write('\n')
    os.chmod(CONFIG, 0o600)


def normalize_regions(data):
    if isinstance(data, dict):
        for field in ('items', 'regions', 'data'):
            if isinstance(data.get(field), list):
                data = data[field]
                break
    if not isinstance(data, list):
        raise DeploymentError('Unexpected Bunny regions response; cannot validate region')
    options = []
    for item in data:
        if isinstance(item, dict):
            code = item.get('id') or item.get('regionId') or item.get('code')
            title = item.get('name') or item.get('displayName') or item.get('country') or str(code)
            if isinstance(code, str) and code:
                options.append((code, str(title)))
    if not options:
        raise DeploymentError('Bunny returned no deployable regions; try again later')
    return options


def extract_app_id(data):
    if isinstance(data, dict):
        for k in ('id', 'appId', 'guid'):
            if isinstance(data.get(k), str) and data[k]:
                return data[k]
    raise DeploymentError('Bunny created a response without a recognizable app ID. Inspect your Bunny dashboard; do not rerun setup blindly.')


def find_https_url(data):
    """Only use explicitly returned endpoint hostnames; never synthesize a URL."""
    candidates = []
    def walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                key = k.lower()
                if isinstance(v, str) and v and any(token in key for token in ('hostname', 'publicurl', 'endpointurl', 'cdnurl')):
                    candidates.append(v)
                if isinstance(v, (dict, list)):
                    walk(v)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)
    walk(data)
    for v in candidates:
        u = v if v.startswith('https://') else 'https://' + v if '://' not in v else ''
        parsed = urllib.parse.urlparse(u)
        if parsed.scheme == 'https' and parsed.hostname and not parsed.username:
            return f'https://{parsed.netloc}'
    return None


def fetch_url(key, app_id):
    for path in (f'/mc/apps/{urllib.parse.quote(app_id, safe="")}/endpoints', f'/mc/apps/{urllib.parse.quote(app_id, safe="")}'):
        try:
            result = find_https_url(request('GET', path, key))
            if result:
                return result
        except DeploymentError:
            continue
    return None



def split_image(image):
    """Validate a public GHCR image and expose the mandatory Bunny v3 fields."""
    match = re.fullmatch(r'ghcr\.io/([a-z0-9][a-z0-9_.-]*)/([a-z0-9][a-z0-9_.-]*):([a-zA-Z0-9_][a-zA-Z0-9_.-]*)', image)
    if match is None:
        raise DeploymentError('Use a fully-qualified public GHCR image, such as ghcr.io/owner/image:tag')
    namespace, name, tag = match.groups()
    return dict(image=image, imageNamespace=namespace, imageName=name, imageTag=tag,
                imagePullPolicy='always')


def registry_ids(registries, host='ghcr.io'):
    """Return existing matching registry IDs, without mutating shared Bunny registries."""
    if isinstance(registries, list):
        entries = registries
    elif isinstance(registries, dict) and isinstance(registries.get('items'), list):
        entries = registries['items']
    else:
        raise DeploymentError('Unexpected Bunny registry response; refusing to create a paid app')
    matches = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        registered_host = str(entry.get('hostName') or '').strip().lower().rstrip('/')
        if registered_host.startswith('https://'):
            registered_host = registered_host[8:]
        value = entry.get('id')
        if registered_host == host and isinstance(value, (str, int)) and not isinstance(value, bool) and str(value):
            if str(value) not in matches:
                matches.append(str(value))
    return matches


def ensure_registry(key, existing, image=IMAGE):
    """Pick an existing or built-in GHCR registry that can resolve the actual image.

    The digest check is a read-only operation in Bunny: no new registry or paid app
    is created here. Multiple GHCR connections are normal and never deleted.
    """
    fields = split_image(image)
    matches = registry_ids(existing)
    if len(matches) > 1:
        print(f'Found {len(matches)} GHCR registry connections. Checking image access without changing them.')
    candidates = list(dict.fromkeys(['github', *matches]))
    for candidate in candidates:
        try:
            result = request('POST', '/mc/registries/digest', key, {
                'registryId': candidate, 'imageName': fields['imageName'],
                'imageNamespace': fields['imageNamespace'], 'tag': fields['imageTag'],
            })
        except DeploymentError:
            print(f'  Registry {candidate}: image lookup unavailable; trying next.')
            continue
        digest = result.get('digest') if isinstance(result, dict) else None
        if isinstance(digest, str) and re.fullmatch(r'sha256:[0-9a-fA-F]{64}', digest):
            print(f'  Registry {candidate}: image verified.')
            return candidate
        print(f'  Registry {candidate}: no valid image digest returned; trying next.')
    raise DeploymentError('No GHCR registry can verify this image. Confirm ghcr.io package is PUBLIC and tag exists; no Bunny app or registry was created. Do not delete existing registries.')


def check_no_duplicate_app(key):
    result = request('GET', '/mc/apps', key)
    if isinstance(result, dict) and isinstance(result.get('items'), list):
        for app in result['items']:
            if isinstance(app, dict) and app.get('name') == 'torrserver-bunny':
                raise DeploymentError('An app named torrserver-bunny already exists in this Bunny account. Inspect it in the Bunny dashboard rather than creating a duplicate paid app.')
    elif isinstance(result, list):
        for app in result:
            if isinstance(app, dict) and app.get('name') == 'torrserver-bunny':
                raise DeploymentError('An app named torrserver-bunny already exists in this Bunny account. Inspect it in the Bunny dashboard rather than creating a duplicate paid app.')
    else:
        raise DeploymentError('Cannot verify existing Bunny apps; refusing to risk duplicate paid app creation')


def build_payload(region, user, password, monitor_token, image=IMAGE, public_peers=False, image_registry_id=None):
    image_fields = split_image(image)
    if not image_registry_id:
        raise DeploymentError('Bunny imageRegistryId must be resolved before building a paid-app request')
    # Secrets are passed to the container as env vars, never to GitHub source.
    env = [
        {'name': 'TS_HTTPAUTH', 'value': '1'},
        {'name': 'TS_AUTH_USER', 'value': user},
        {'name': 'TS_AUTH_PASSWORD', 'value': password},
        {'name': 'BUNNY_WATCHDOG_TOKEN', 'value': monitor_token},
        {'name': 'TS_TORR_ADDR', 'value': ':32000'},
    ]
    endpoints = [{
        'displayName': 'torrserver-https',
        'cdn': {'isSslEnabled': True, 'portMappings': [{'containerPort': 8080, 'exposedPort': 80, 'protocols': ['tcp']}]},
    }]
    if public_peers:
        endpoints.append({
            'displayName': 'torrent-peers',
            'anycast': {'type': 'iPv4', 'portMappings': [{'containerPort': 32000, 'exposedPort': 32000, 'protocols': ['tcp', 'udp']}]},
        })
    return {
        'name': 'torrserver-bunny',
        'runtimeType': 'shared',
        'autoScaling': {'min': 1, 'max': 1},
        'regionSettings': {'allowedRegionIds': [region], 'requiredRegionIds': [region], 'maxAllowedRegions': 1},
        'terminationGracePeriodSeconds': 30,
        'containerTemplates': [{
            'name': 'torrserver',
            **image_fields,
            'imageRegistryId': str(image_registry_id),
            'environmentVariables': env,
            'endpoints': endpoints,
            'volumeMounts': [{'name': 'config', 'mountPath': '/opt/ts/config'}],
        }],
        'volumes': [{'name': 'config', 'size': 1}],
    }


def setup(args):
    if CONFIG.exists():
        raise DeploymentError('Already configured; refusing to create a second paid application. Use start/status/stop or back up the config intentionally.')
    print('\nTorrServer Bunny · First-time setup')
    print('CLI build:', CLI_BUILD)
    print('Bunny API key stays locally in a chmod 600 file; never paste it into a public issue or chat.')
    key = ask('Bunny account API key', hidden=True)
    if not key:
        raise DeploymentError('API key is required')
    image_fields = split_image(args.image)
    print('Checking Bunny API, existing apps, GHCR registry and available regions...')
    check_no_duplicate_app(key)
    existing_registries = request('GET', '/mc/registries', key)
    reg_id = ensure_registry(key, existing_registries, args.image)
    regions = normalize_regions(request('GET', '/mc/regions', key))
    for i, (code, title) in enumerate(regions, 1):
        print(f'  {i:>2}. {title} ({code})')
    selection = ask('Select region by number/code', '1')
    region = None
    if selection.isdigit() and 1 <= int(selection) <= len(regions):
        region = regions[int(selection) - 1][0]
    else:
        region = next((code for code, _ in regions if code.lower() == selection.lower()), None)
    if not region:
        raise DeploymentError('Invalid region')
    user = ask('TorrServer username', 'lampa')
    if not user or len(user) > 64 or any(ch not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for ch in user):
        raise DeploymentError('Invalid username')
    password = secrets.token_urlsafe(22)
    monitor_token = secrets.token_urlsafe(32)
    peer = ask('Expose BitTorrent TCP/UDP peer port via paid Anycast IPv4? (y/N)', 'N').lower() == 'y'
    print('\nCreating one-region application (persistent config volume: 1 GB billed while stopped).')
    print('Image:', image_fields['image'], '(public GHCR)')
    print('Registry already verified:', reg_id)
    print('This will create paid Bunny resources. Type CREATE to continue.')
    if ask('Confirm') != 'CREATE':
        print('Canceled. No application created.')
        return
    # Refresh app listing immediately before POST to avoid accidental duplicates.
    check_no_duplicate_app(key)
    payload = build_payload(region, user, password, monitor_token, args.image, peer, reg_id)
    app = request('POST', '/mc/apps', key, payload)
    app_id = extract_app_id(app)
    config = dict(api_key=key, app_id=app_id, region=region, username=user, password=password,
                  watchdog_token=monitor_token, image=args.image, url=find_https_url(app),
                  public_peers=peer, created_at=datetime.now(timezone.utc).isoformat())
    save_config(config)
    print(f'\nApp created: {app_id} · region {region}')
    print('Saved credentials locally (mode 600).')
    if not args.no_deploy:
        try:
            request('POST', f'/mc/apps/{urllib.parse.quote(app_id, safe="")}/deploy', key)
            print('Deploy requested. Container provisioning is asynchronous.')
        except DeploymentError as exc:
            print('Deploy unsuccessful; configuration saved. Use "torrserver-bunny start" to retry.', file=sys.stderr)
            print(str(exc), file=sys.stderr)
    try:
        config['url'] = config['url'] or fetch_url(key, app_id)
        save_config(config)
    except DeploymentError:
        pass
    print_details(config)
    print('\nAutomatic 60-minute idle shutdown requires an external scheduler. See: bunny/README.md')


def print_details(c):
    print('\n=== Lampa connection ===')
    if c.get('url'):
        print('TorrServer URL:', c['url'])
    else:
        print('TorrServer URL: read the HTTPS CDN endpoint in Bunny dashboard;')
        print('then run: torrserver-bunny set-url https://YOUR-REAL-ENDPOINT')
    print('Username:', c['username'])
    print('Password:', c['password'])
    print('Configure this URL + credentials in Lampa → Settings → TorrServer.')


def lifecycle(action):
    c = load_config()
    verb = 'deploy' if action == 'start' else 'undeploy'
    request('POST', f'/mc/apps/{urllib.parse.quote(c["app_id"], safe="")}/{verb}', c['api_key'])
    print(f'{verb.upper()} requested for {c["app_id"]}. Bunny transitions asynchronously.')
    if action == 'start':
        if not c.get('url'):
            c['url'] = fetch_url(c['api_key'], c['app_id'])
            save_config(c)
        print_details(c)


def status():
    c = load_config()
    data = request('GET', f'/mc/apps/{urllib.parse.quote(c["app_id"], safe="")}', c['api_key'])
    print('App ID:', c['app_id'], 'Region:', c['region'])
    print('State:', (data or {}).get('status', 'See Bunny dashboard') if isinstance(data, dict) else 'See Bunny dashboard')
    if not c.get('url'):
        c['url'] = fetch_url(c['api_key'], c['app_id'])
        save_config(c)
    print_details(c)


def set_url(url):
    p = urllib.parse.urlparse(url)
    if p.scheme != 'https' or not p.hostname or p.username or p.password or p.query or p.fragment:
        raise DeploymentError('Enter a valid HTTPS CDN endpoint URL without credentials or query string')
    c = load_config()
    c['url'] = url.rstrip('/')
    save_config(c)
    print('Public URL saved:', c['url'])


def get_activity(url, token):
    base = url.rstrip('/')
    # Cachebuster defends against CDN caches and stale activity data.
    stamp = str(int(time.time() * 1000))
    return request('GET', f'{base}/__bunny/activity?ts={stamp}', extra_headers={'X-Watchdog-Token': token, 'Cache-Control': 'no-cache'})


def can_stop(stats, now, idle_seconds):
    if not isinstance(stats, dict):
        raise DeploymentError('Unexpected activity response; refusing to stop')
    active = stats.get('active_streams')
    last = stats.get('last_media_unix')
    if not isinstance(active, int) or not isinstance(last, (int, float)) or isinstance(active, bool):
        raise DeploymentError('Missing activity fields; refusing to stop')
    if last <= 0 or last > now + 60 or active < 0:
        raise DeploymentError('Invalid activity timestamps; refusing to stop')
    return active == 0 and now - last >= idle_seconds


def idle_check(args):
    # GitHub Actions invocation: no saved config and no plaintext API key in repository.
    if args.remote:
        key, app_id, url, token = (os.getenv(n, '') for n in ('BUNNY_API_KEY', 'BUNNY_APP_ID', 'BUNNY_PUBLIC_URL', 'BUNNY_WATCHDOG_TOKEN'))
    else:
        c = load_config()
        key, app_id, url, token = c['api_key'], c['app_id'], c.get('url'), c['watchdog_token']
    if not all((key, app_id, url, token)):
        raise DeploymentError('Missing app, HTTPS public URL or watchdog credentials; refusing to stop')
    print('Checking live activity...')
    first = get_activity(url, token)
    now = time.time()
    if not can_stop(first, now, args.minutes * 60):
        print('Active stream or idle threshold not reached. Leaving server running.')
        return
    # Minimize race with player beginning a stream while first response is processed.
    time.sleep(5 if not args.no_pause else 0)
    second = get_activity(url, token)
    if not can_stop(second, time.time(), args.minutes * 60):
        print('Activity changed. Leaving server running.')
        return
    request('POST', f'/mc/apps/{urllib.parse.quote(app_id, safe="")}/undeploy', key)
    print(f'IDLE_STOP_REQUESTED app={app_id} idle_min={args.minutes}')


def github_watchdog(args):
    c = load_config()
    if not c.get('url'):
        raise DeploymentError('Run set-url first: cannot monitor without HTTPS endpoint')
    if subprocess.run(['which', 'gh'], capture_output=True).returncode:
        raise DeploymentError('GitHub CLI (gh) is required. Install and authenticate, or configure secrets manually.')
    repo = args.repo or ask('Your OWN GitHub repository with the watchdog workflow (owner/repo)', 'vbrekher/TorrServer-bunny')
    if not repo or '/' not in repo:
        raise DeploymentError('Invalid repository name')
    print('Setting GitHub Actions secrets on:', repo)
    print('Only use a repository you control. Review its workflows before placing account API keys there.')
    if ask('Type ENABLE to install GitHub secrets') != 'ENABLE':
        print('Canceled')
        return
    values = {
        'BUNNY_API_KEY': c['api_key'], 'BUNNY_APP_ID': c['app_id'],
        'BUNNY_PUBLIC_URL': c['url'], 'BUNNY_WATCHDOG_TOKEN': c['watchdog_token']
    }
    for name, value in values.items():
        proc = subprocess.run(['gh', 'secret', 'set', name, '-R', repo], input=value, text=True, capture_output=True)
        if proc.returncode:
            raise DeploymentError(f'Could not install {name} as secret: {proc.stderr[:400]}')
    print('Secrets installed. Enable Actions for this repo and check idle-watchdog.yml schedule on default branch.')
    print('Idle-check every ~10 minutes: stop after >=60 minutes without media activity, if workflow runs.')


def main(argv=None):
    parser = argparse.ArgumentParser(description='Deploy TorrServer to Bunny Magic Containers (no dependencies)')
    sub = parser.add_subparsers(dest='command', required=True)
    init = sub.add_parser('setup', help='Prompt for API key and region, create and deploy app')
    init.add_argument('--image', default=IMAGE, help='Public, published compatible image (default project GHCR)')
    init.add_argument('--no-deploy', action='store_true')
    sub.add_parser('start', help='Start your existing server')
    sub.add_parser('stop', help='Stop server compute (volume remains billed)')
    sub.add_parser('status', help='Show app status and connection details')
    u = sub.add_parser('set-url', help='Store exact HTTPS URL shown in Bunny dashboard')
    u.add_argument('url')
    check = sub.add_parser('idle-check', help='Check media activity and undeploy if idle')
    check.add_argument('--minutes', type=int, default=60)
    check.add_argument('--remote', action='store_true', help='Read credentials from GitHub Actions environment')
    check.add_argument('--no-pause', action='store_true', help=argparse.SUPPRESS)
    w = sub.add_parser('enable-github-watchdog', help='Store secrets in your OWN GitHub repository for schedule')
    w.add_argument('--repo')
    args = parser.parse_args(argv)
    try:
        if args.command == 'setup': setup(args)
        elif args.command in ('start', 'stop'): lifecycle(args.command)
        elif args.command == 'status': status()
        elif args.command == 'set-url': set_url(args.url)
        elif args.command == 'idle-check':
            if not 5 <= args.minutes <= 1440:
                raise DeploymentError('Idle timeout must be between 5 and 1440 minutes')
            idle_check(args)
        elif args.command == 'enable-github-watchdog': github_watchdog(args)
    except (DeploymentError, KeyboardInterrupt, EOFError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
