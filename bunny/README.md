# TorrServer Bunny — technical deployment and controls

User-friendly guides: [Русский](../docs/README.ru.md) · [English](../docs/README.en.md) · [Nederlands](../docs/README.nl.md)

**Status (4 Nov 2026): real Bunny app, HTTPS CDN, and Lampa playback were confirmed by the owner. Live idle shutdown is now also confirmed: [GitHub Actions #41920393921](https://github.com/vbrekher/TorrServer-bunny/actions/runs/41920393921) reported 91 idle minutes and `IDLE_STOP_REQUESTED`, followed by owner-observed Bunny `State: inactive`. Independent Samsung Tizen/codec coverage remains unverified; cron scheduling is best effort.** The stock TorrServer source remains upstream-compatible. Read [YouROK/TorrServer](https://github.com/YouROK/TorrServer) for original functionality and GPL-3.0 license.

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

Use the **HTTPS CDN URL**, username and locally stored password in **Lampa → Settings → TorrServer**. The ordinary `status` command hides the password; run `torrserver-bunny status --show-credentials` only on your own computer if needed. **Never enter the Anycast BitTorrent peer endpoint (an IP address with :32000) as the Lampa URL.** After app creation, `status` refreshes endpoint inventory and repairs an Anycast IP accidentally saved as the HTTPS URL. If the CDN hostname is not yet provisioned, check the Bunny app's `torrserver-https` CDN endpoint. Do not create another app. For compatibility tests, check `https://ACTUAL-ENDPOINT/echo` and try a permitted, legally distributed torrent. Chrome and Samsung Tizen have differing CORS, mixed-content and media requirements; playback **has not been verified** on a physical Samsung TV.

## Recovering from POST /mc/apps HTTP 500

**Do not repeatedly create paid apps.** First run `~/.local/bin/torrserver-bunny doctor`, which lists existing apps, numeric GHCR registry IDs, and account resource quotas without creating anything. Inspect Magic Containers in the Bunny dashboard as well. An HTTP 500 may be ambiguous even if the immediate listing shows zero results.

The Bunny registry digest endpoint can accept a symbolic registry alias such as `github`, but that does **not** establish it as a valid `containerTemplates[].imageRegistryId` for app creation. The supported official CLI enumerates connected registries with numeric IDs. This installer now requires a numeric `ghcr.io` registry ID returned by `GET /mc/registries`, checks the image digest through that exact numeric ID, and refuses to create if none works. Never delete or replace GHCR connections used by other apps.

A successful mocked CI test does not prove that Bunny production will accept the payload. If Bunny still returns 500 after selecting a real numeric registry ID, stop creation and send Bunny Support the UTC time, `POST /mc/apps`, HTTP 500 response, region and a redacted payload (remove all API credentials, environment variables, authentication tokens and personal values). The support team can inspect server-side causes that are not exposed by the public API.

## 60-minute idle shutdown without an always-on container

Bunny's autoscaling **is not** an idle-shutdown timer. `undeploy` is the supported way to stop running containers while keeping the app and its config volume.

This repo provides a small HTTP gateway in front of TorrServer. It counts **media bytes transferred** via `/stream`, `/play`, `/playlist*`, `/gst/*`, and reports a token-protected activity summary on `/__bunny/activity`. The read-only CLI command `torrserver-bunny activity` queries this endpoint and prints active requests, tracked bytes and idle minutes without exposing its token. New gateway versions also provide aggregate, privacy-safe counters: `proxy_requests`, `media_requests`, `other_requests`, `other_response_bytes`, and `unclassified_media_bytes` (no URLs, queries, titles, hashes or user IDs). When a verified stream remains at 0 bytes, use `torrserver-bunny activity --probe` to send an unauthenticated cache-busted `/echo` request and compare the proxy request counter. Unknown media-like bytes fail closed, and **never** qualify an application for automatic shutdown. These counters only appear after the new Docker image has been deployed to the existing Bunny app; updating the CLI alone is insufficient. If no video was played since container startup, a zero tracked-media count is expected. Health probes and normal `/echo` checks **do not** reset the idle timer. Existing in-flight media streams prevent shutdown, even if network temporarily stalls. Bunny API keys are **not** present in the application container. The container has only the Lampa username/password and a separate non-management watchdog token.

On the user's **own GitHub repo** (fork if you aren't this repo's owner), scheduled GitHub Actions checks every ~10 minutes, then issues `POST /mc/apps/{id}/undeploy` only after **>=60 minutes** of media inactivity and **at least some media bytes tracked since this container started**. After the first positive check it checks again before stopping. No action is taken on failed/unexpected responses. GitHub Actions cron runs may be delayed or disabled, so idle-off is best effort, not a strict timer or billing guarantee. Secrets must be set in the owner's repo only, never in a shared third-party repo:

```bash
~/.local/bin/torrserver-bunny enable-github-watchdog --repo YOUR-ACCOUNT/YOUR-FORK
```

Before enabling, start the current app, play a real Lampa test stream, then execute `~/.local/bin/torrserver-bunny activity` to verify a reachable endpoint and `Tracked media bytes since container startup` **greater than zero**. The CLI refuses to enable a scheduled shutdown without proof of tracked media. It also refuses to automatically undeploy an instance that has tracked zero media bytes, preventing a false shutdown if the stream bypasses the gateway. This means an instance that has not carried a tracked stream after restart will **not** be stopped automatically; stop it manually if needed. Real GitHub runs on 3 Nov 2026 failed because all four secrets were absent. To finish setup use `enable-github-watchdog --repo vbrekher/TorrServer-bunny`, then `gh workflow enable idle-watchdog.yml -R vbrekher/TorrServer-bunny` and `gh workflow run idle-watchdog.yml -R vbrekher/TorrServer-bunny`. Verify the workflow logs and the Bunny app status after 60+ idle minutes. The job logs `IDLE_STOP_REQUESTED` when requesting undeploy. The first observed live stop is documented in [run #41920393921](https://github.com/vbrekher/TorrServer-bunny/actions/runs/41920393921). Subsequent runs against an already undeployed gateway may get HTTP 503; the updated watchdog checks the Bunny app status via API and logs `ALREADY_INACTIVE` only on explicit status `inactive`, without issuing any POST. If status is `active`, `progressing`, or cannot be established, it fails closed instead of claiming success. Requires `gh auth login` and [GitHub CLI](https://cli.github.com/), with permission to set Actions secrets. The workflow must be present on the repo default branch and Actions must be enabled. The wizard stores `BUNNY_API_KEY`, `BUNNY_APP_ID`, `BUNNY_PUBLIC_URL`, and `BUNNY_WATCHDOG_TOKEN` as repository Actions secrets. This account API key has broad privileges: restrict access to that repository and review workflows before enabling. If you don't want GitHub or your laptop remains on, you may run `torrserver-bunny idle-check` from your own cron/launchd every 10 minutes. Manual stop always works independently.

**Known limitation:** if a streaming client or CDN bypasses the gateway, activity is not counted. Disable CDN caching for the media endpoint and confirm test playback passes through the gateway. The chosen cache-control header is `private, no-store`, but verify Bunny Pull Zone caching behavior on a real deployment. The `POST /undeploy` may race with a new stream starting after the final check. This is for personal, single-viewer use, not a general multi-user on-demand streaming platform.

## Cost notes

Bunny published rates (checked 2 Nov 2026): CPU **$0.02/core-hour** (actual CPU usage), RAM **$0.005/GB-hour** (billed in 64 MB increments), Europe/North America outbound bandwidth **$0.01/GB**, a 1 GB persistent volume **$0.10/month even when undeployed**, optional Anycast IPv4 **$2/month prorated by minute while allocated**. For one 50 GB film streamed over three hours to one EU/NA viewer, assume one fully consumed CPU core and 1 GB of billed RAM: $0.50 bandwidth + $0.06 CPU + $0.015 RAM = **$0.575 (about $0.58) per example movie session, before recurring resources**. If this is the only film watched over 30 days with allocated storage all month, illustrative monthly totals are **~$0.68 without Anycast** or **~$2.68 with Anycast** (full-month IP). These are examples, not bills. Additional torrent peer upload/seeding, repeat traffic, applicable CDN charges, taxes, other products and account-level minimums are excluded. Actual billing and rates may differ; see [Bunny Magic Containers pricing](https://bunny.net/magic-containers/) and [Bunny CDN pricing](https://bunny.net/pricing/cdn/). Use only torrents you may legally download and share.

## Architecture & validation

- `Dockerfile.bunny`: upstream GHCR image + tiny standard-library Go transparent HTTP gateway; no upstream engine rewrite
- `bunny/entrypoint.sh`: creates local Basic auth configuration in persistent config volume; starts TorrServer on internal 8090; exposes gateway on 8080
- `bunny/cli.py`: dependency-free Python 3 Bunny Magic Containers API client
- `.github/workflows/build-bunny-image.yml`: publish public container image (package visibility may require owner action)
- `.github/workflows/idle-watchdog.yml`: external scheduled idle shutdown
- tests: `python3 -m unittest discover -s tests`; `cd bunny && go test ./...`

Bunny API reference: [Add Application](https://bunny.net/docs/api-reference/magic-containers/applications/add-application), [Magic Containers](https://bunny.net/magic-containers/). Do not claim real deploy/TV playback until these external acceptance checks are passed with real credentials and a running container.
