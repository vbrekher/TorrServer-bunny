# TorrServer Bunny — deployment and controls

**Status: source implementation; live Bunny API/TV playback requires the owner's API key and tests.** The stock TorrServer source remains upstream-compatible. Read [YouROK/TorrServer](https://github.com/YouROK/TorrServer) for original functionality and GPL-3.0 license.

## User installation (macOS/Linux)

```bash
curl -fsSL https://raw.githubusercontent.com/vbrekher/TorrServer-bunny/master/install-bunny.sh -o install-bunny.sh
sh ./install-bunny.sh
```

Requires Python 3 and curl; no sudo, Docker or GitHub Actions for manual start/stop. The installer prompts for Bunny account API key (hidden), **a live region list from `/mc/regions`**, username, optional public peer port (Anycast IP cost), and confirmation before provisioning. It creates one Magic Containers application with **one required region**, one 1-GB persistent *config* volume and HTTPS CDN endpoint. The custom image is published to `ghcr.io/vbrekher/torrserver-bunny:main` by the build workflow in this repository; its GHCR package must be **public**. If the image isn't yet published/public, setup will not result in a usable server; publish it first.

Commands:

```bash
~/.local/bin/torrserver-bunny setup     # once
~/.local/bin/torrserver-bunny start     # movie night
~/.local/bin/torrserver-bunny status
~/.local/bin/torrserver-bunny stop      # when done
```

After provisioning, the installer attempts to read the HTTPS CDN hostname returned by Bunny. If the API doesn't return it, copy the exact URL visible in the Bunny Magic Containers dashboard and save it:

```bash
~/.local/bin/torrserver-bunny set-url https://ACTUAL-ENDPOINT-FROM-BUNNY
```

Use the URL, username and password printed by `status` in **Lampa → Settings → TorrServer**. For compatibility tests, check `https://ACTUAL-ENDPOINT/echo` and try a permitted, legally distributed torrent. Chrome and Samsung Tizen have differing CORS, mixed-content and media requirements; playback **has not been verified** on a physical Samsung TV.

## Recovering from POST /mc/apps HTTP 500

**Do not repeatedly create paid apps.** First run `~/.local/bin/torrserver-bunny doctor`, which lists existing apps, numeric GHCR registry IDs, and account resource quotas without creating anything. Inspect Magic Containers in the Bunny dashboard as well. An HTTP 500 may be ambiguous even if the immediate listing shows zero results.

The Bunny registry digest endpoint can accept a symbolic registry alias such as `github`, but that does **not** establish it as a valid `containerTemplates[].imageRegistryId` for app creation. The supported official CLI enumerates connected registries with numeric IDs. This installer now requires a numeric `ghcr.io` registry ID returned by `GET /mc/registries`, checks the image digest through that exact numeric ID, and refuses to create if none works. Never delete or replace GHCR connections used by other apps.

A successful mocked CI test does not prove that Bunny production will accept the payload. If Bunny still returns 500 after selecting a real numeric registry ID, stop creation and send Bunny Support the UTC time, `POST /mc/apps`, HTTP 500 response, region and a redacted payload (remove all API credentials, environment variables, authentication tokens and personal values). The support team can inspect server-side causes that are not exposed by the public API.

## 60-minute idle shutdown without an always-on container

Bunny's autoscaling **is not** an idle-shutdown timer. `undeploy` is the supported way to stop running containers while keeping the app and its config volume.

This repo provides a small HTTP gateway in front of TorrServer. It counts **media bytes transferred** via `/stream`, `/play`, `/playlist*`, `/gst/*`, and reports a token-protected activity summary on `/__bunny/activity`. Health probes and normal `/echo` checks **do not** reset the idle timer. Existing in-flight media streams prevent shutdown, even if network temporarily stalls. Bunny API keys are **not** present in the application container. The container has only the Lampa username/password and a separate non-management watchdog token.

On the user's **own GitHub repo** (fork if you aren't this repo's owner), scheduled GitHub Actions checks every ~10 minutes, then issues `POST /mc/apps/{id}/undeploy` only after **>=60 minutes** of media inactivity. After the first positive check it checks again before stopping. No action is taken on failed/unexpected responses. GitHub Actions cron runs may be delayed or disabled, so idle-off is best effort, not a strict timer or billing guarantee. Secrets must be set in the owner's repo only, never in a shared third-party repo:

```bash
~/.local/bin/torrserver-bunny enable-github-watchdog --repo YOUR-ACCOUNT/YOUR-FORK
```

Requires `gh auth login` and [GitHub CLI](https://cli.github.com/), with permission to set Actions secrets. The workflow must be present on the repo default branch and Actions must be enabled. The wizard stores `BUNNY_API_KEY`, `BUNNY_APP_ID`, `BUNNY_PUBLIC_URL`, and `BUNNY_WATCHDOG_TOKEN` as repository Actions secrets. This account API key has broad privileges: restrict access to that repository and review workflows before enabling. If you don't want GitHub or your laptop remains on, you may run `torrserver-bunny idle-check` from your own cron/launchd every 10 minutes. Manual stop always works independently.

**Known limitation:** if a streaming client or CDN bypasses the gateway, activity is not counted. Disable CDN caching for the media endpoint and confirm test playback passes through the gateway. The chosen cache-control header is `private, no-store`, but verify Bunny Pull Zone caching behavior on a real deployment. The `POST /undeploy` may race with a new stream starting after the final check. This is for personal, single-viewer use, not a general multi-user on-demand streaming platform.

## Cost notes

Bunny published rates (2 Nov 2026): CPU $0.02/core-hour, RAM $0.005/GB-hour, EU/NA egress $0.01/GB, 1-GB volume about $0.10/month even when undeployed, optional Anycast IPv4 $2/month prorated. 50 GB HTTP egress = $0.50; three hours at full 1 vCPU + 1 GB = $0.075; **$0.575 + allocated storage + torrent peer upload + optional Anycast**. CPU is actual consumed time, so $0.075 represents a full-usage example, not a promised final bill. Shared torrent peer upload can materially increase outgoing traffic. Consult [Bunny pricing](https://bunny.net/magic-containers/) and your account billing. The runtime should only be used for content you have rights to access or share.

## Architecture & validation

- `Dockerfile.bunny`: upstream GHCR image + tiny standard-library Go transparent HTTP gateway; no upstream engine rewrite
- `bunny/entrypoint.sh`: creates local Basic auth configuration in persistent config volume; starts TorrServer on internal 8090; exposes gateway on 8080
- `bunny/cli.py`: dependency-free Python 3 Bunny Magic Containers API client
- `.github/workflows/build-bunny-image.yml`: publish public container image (package visibility may require owner action)
- `.github/workflows/idle-watchdog.yml`: external scheduled idle shutdown
- tests: `python3 -m unittest discover -s tests`; `cd bunny && go test ./...`

Bunny API reference: [Add Application](https://bunny.net/docs/api-reference/magic-containers/applications/add-application), [Magic Containers](https://bunny.net/magic-containers/). Do not claim real deploy/TV playback until these external acceptance checks are passed with real credentials and a running container.
