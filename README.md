# 🎬 TorrServer Bunny

**Movie night on demand. TorrServer on bunny.net Magic Containers, for Lampa and Smart TVs.**

Install in one terminal session, choose your Bunny region, and receive a private TorrServer endpoint. Start it for a movie, stop it when you're done; optionally enable an external watchdog that shuts down after **60 minutes without media streaming**.

This project wraps the open-source [TorrServer by YouROK](https://github.com/YouROK/TorrServer) with a Bunny deployment and lifecycle layer. **Huge thanks to YouROK and all TorrServer contributors.** The engine is theirs; the Bunny installer and activity gateway are the additions here. Licensed under GPL-3.0; see [LICENSE](LICENSE).

## Quick start

Prerequisites: a [bunny.net](https://bunny.net/) account with Magic Containers access; a Bunny account API key; macOS or Linux with `python3` and `curl`.

```bash
curl -fsSL https://raw.githubusercontent.com/vbrekher/TorrServer-bunny/master/install-bunny.sh -o install-bunny.sh
sh ./install-bunny.sh
```

The wizard asks for your **Bunny API key (hidden)**, a **region** from Bunny's live region list, a TorrServer username, and whether you want the optional paid peer Anycast IP. It then asks for explicit `CREATE` approval before provisioning anything paid. It creates a single-region Magic Containers app using `ghcr.io/vbrekher/torrserver-bunny:main`, persistent configuration storage, and an HTTPS endpoint. You must **publish this public GHCR image first** using the included build workflow; initial live image availability has not been verified.

Use these commands afterward:

```bash
~/.local/bin/torrserver-bunny start    # start on movie night
~/.local/bin/torrserver-bunny status   # show URL + Lampa credentials
~/.local/bin/torrserver-bunny stop     # turn off compute
```

The installer prints the actual HTTPS endpoint if Bunny's API returns it. If not, copy it from your Magic Containers dashboard and run:

```bash
~/.local/bin/torrserver-bunny set-url https://YOUR-ACTUAL-BUNNY-ENDPOINT
```

Then enter **URL, username, password** in **Lampa → Settings → TorrServer**. Do not expose an unauthenticated HTTP TorrServer directly to the internet. This deployment enables Basic auth and uses Bunny's HTTPS CDN endpoint.

## Automatic idle shutdown (optional)

Bunny does not provide a guaranteed built-in "stop after 60 minutes without movie streams" setting. We keep the **Bunny API key outside the container** and use a lightweight gateway to record real media stream activity. Every ~10 minutes, a scheduled GitHub Actions workflow on *your own repository/fork* can check the gateway. If no media has been transferred for at least 60 minutes and no media request is active, it issues Bunny `undeploy`. No traffic or scheduler failure causes a shutdown: **fail closed**.

```bash
# Requires gh installed, logged in and workflow on YOUR repo's default branch
~/.local/bin/torrserver-bunny enable-github-watchdog --repo YOUR-ACCOUNT/YOUR-FORK
```

The GitHub Actions schedule is **best effort** (can be delayed/disabled); manual stop is always available. Never install account-level Bunny credentials as Actions secrets in a repo you do not own or trust. See [full deployment and security guide](bunny/README.md).

## Example pricing: 50 GB movie, European region

| Item | Example calculation |
| --- | ---: |
| 50 GB outbound HTTP media at $0.01/GB | $0.50 |
| Three hours assuming full 1 CPU core at $0.02/core-hour | $0.06 |
| Three hours at 1 GB RAM at $0.005/GB-hour | $0.015 |
| **Example session subtotal** | **$0.575** |
| 1-GB persistent volume | about $0.10/month, even stopped |
| Optional Anycast IPv4 for inbound TCP/UDP peers | $2/month, billed per minute |

Torrent peer upload and other outbound traffic are additional; CPU is billed on actual usage, so the CPU example is an assumption, not a fixed fee. See [published Bunny rates](https://bunny.net/magic-containers/).

## What this project does / doesn't do

- ✅ Region selection, HTTPS endpoint creation, Basic auth, one-region deployment, start/stop/status, persistent configuration
- ✅ Built-in media activity gateway and optional externally scheduled 60-minute idle shutdown
- ✅ Linux/macOS self-service installer without running Docker or a VPS
- ⚠️ An image must be published and made public in GitHub Container Registry before the deployment works
- ⚠️ Real Bunny provisioning, public endpoint URL response, BitTorrent peer connectivity, Samsung Tizen/Lampa playback and accurate idle-shutdown billing are **not yet live-tested**
- ⚠️ Basic auth over HTTPS requires compatible Lampa configuration. A CDN/cache or browser CORS issue may need account-specific adjustments
- ❌ No copyrighted videos, pirate catalogs, or media are hosted or distributed by this repository

For a full explanation, screenshots from actual setup after verified deployment, the runtime architecture and test instructions, see [bunny/README.md](bunny/README.md). The [original TorrServer documentation](https://github.com/YouROK/TorrServer) remains the reference for torrent engine features.

[Русское руководство](docs/README.ru.md) · [Bunny Magic Containers documentation](https://bunny.net/docs/magic-containers)
