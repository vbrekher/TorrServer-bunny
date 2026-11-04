# TorrServer Bunny — Easy user guide (English)

[🇷🇺 Русский](README.ru.md) · **🇬🇧 English** · [🇳🇱 Nederlands](README.nl.md) · [Project home](../README.md)

Turn your [bunny.net Magic Containers](https://bunny.net/magic-containers/) account into a private [TorrServer](https://github.com/YouROK/TorrServer) for [Lampa](https://github.com/yumata/lampa) and compatible devices, without renting a VPS.

**In short:** install once on a Mac or Linux computer → enter the HTTPS server address in Lampa → run **start** when you want to watch → run **stop** afterwards. Your server and settings remain saved.

> **Current verification:** a real Bunny app was created and Bunny returned **active** with an HTTPS CDN endpoint on 2 November 2026. **On 4 November 2026, the owner confirmed streaming playback in Lampa works.** Independent Samsung Tizen model/codec compatibility auditing is not complete. A successful real-world automatic idle stop has **not yet been verified**. This guide does not promise that all torrents, Lampa builds, or TV video formats work.

## 1. What you need

- A [bunny.net account](https://dash.bunny.net/) with **Magic Containers**, and your Bunny **account API key** (keep it private).
- A Mac or Linux computer with **Python 3** and `curl`. You do **not** need Docker or a VPS for the standard setup.
- Lampa on your TV, computer, or another supported device, with an accessible TorrServer setting.
- Internet access and a torrent you have the rights to access and share.

The public Docker image used by this project is `ghcr.io/vbrekher/torrserver-bunny:main`. If Bunny cannot verify the image from a configured GHCR registry, setup stops before creating a paid app.

## 2. Install your server — only once

Open **Terminal** on your Mac/Linux PC. Copy this entire command:

```bash
curl -fsSL --retry 3 \
  https://raw.githubusercontent.com/vbrekher/TorrServer-bunny/master/install-bunny.sh \
  -o /tmp/install-torrserver-bunny.sh \
  && sh /tmp/install-torrserver-bunny.sh
```

The wizard will ask:

| Question | What to enter |
| --- | --- |
| **Bunny account API key** | Paste your private Bunny key into the hidden prompt. Never share it in chat or screenshots. |
| **Select region** | Pick one of the available regions (e.g. `AMS` for Amsterdam, or `DE` for Germany). |
| **TorrServer username** | Press Enter for `lampa`, or choose your own name. |
| **Expose BitTorrent TCP/UDP port via Anycast?** | `N` for a lower-cost first test. `y` if you want a paid IPv4 endpoint for incoming torrent peers. |
| **Confirm** | Type `CREATE` **once** to approve billable Bunny resources. |

The installer registers a single-region Magic Containers app, a **1 GB persistent configuration volume**, and an **HTTPS CDN endpoint**; if you selected `y`, it also requests an optional, separately billed Anycast IPv4 peer endpoint. It generates a TorrServer password and saves the credentials **locally**, in a file with restrictive permissions.

If you already installed this app, **do not run the first-time setup again**. Use the commands in section 4.

## 3. Connect Lampa

Once the app has been created, check its current status:

```bash
~/.local/bin/torrserver-bunny status
```

Look for `State: active` and **`TorrServer HTTPS CDN URL:`**. A valid example looks like `https://mc-example.bunny.run` — this is only an example, **not** your server address.

To see your password **on your own computer**, run:

```bash
~/.local/bin/torrserver-bunny status --show-credentials
```

In **Lampa → Settings → TorrServer** (menu labels can vary between versions), enter:

| Field | Value |
| --- | --- |
| Server / URL | **Your HTTPS CDN domain** from `status` |
| Login / username | Your chosen name, e.g. `lampa` |
| Password | Your password from the local installer or `--show-credentials` |

**Important:** a link such as `https://203.0.113.10:32000` is **not** the Lampa URL. Port `32000` is for BitTorrent peers, not the web player. Always use the HTTPS **CDN domain**.

If `status` does not yet show the CDN address, find the `torrserver-https` endpoint in **Bunny Dashboard → Magic Containers → your app → Endpoints**. You can save that real HTTPS domain:

```bash
~/.local/bin/torrserver-bunny set-url https://YOUR-REAL-CDN-DOMAIN
```

Open the HTTPS address in your browser to test that the web endpoint responds, then try **one lawful, freely distributable torrent** in Lampa. An `active` Bunny app does **not** by itself confirm playback or Tizen compatibility.

## 4. Everyday use: start, stop, check

You do not reinstall or create another Bunny app for each movie.

| You want to... | Run this on the same computer |
| --- | --- |
| **Start** the server before watching | `~/.local/bin/torrserver-bunny start` |
| **Check** if it is running and see its URL | `~/.local/bin/torrserver-bunny status` |
| **Stop** the server after watching | `~/.local/bin/torrserver-bunny stop` |
| **See the password** privately | `~/.local/bin/torrserver-bunny status --show-credentials` |

**How it works:** `start` requests a deploy of the **existing** app, `stop` requests an undeploy, and `status` checks Bunny. Starting and stopping are asynchronous: after `start`, check `status` until the app is active. Lampa does **not** automatically start a stopped container.

`stop` does **not delete** your app, your configuration, or your persistent volume. Its HTTPS CDN domain should remain the same. The allocated volume and Anycast IP (if enabled) may still incur charges while compute is stopped.

## 5. How much does watching one 50 GB Blu-ray-size movie cost?

**Illustrative example:** one full 50 GB stream to one viewer in **Europe or North America**, watched over **3 hours**, assuming an average **1 GB of billed RAM** and a full **1 CPU core worth of usage during those 3 hours**. The actual billed CPU and RAM consumption can differ.

| Charge | Calculation | Example |
| --- | ---: | ---: |
| Outbound video traffic | 50 GB × $0.01/GB | **$0.50** |
| CPU (assumption) | 3 hours × 1 core × $0.02 | **$0.06** |
| RAM (assumption) | 3 hours × 1 GB × $0.005 | **$0.015** |
| **Illustrative movie session** | **50 GB + 3 hours of compute** | **$0.575 ≈ $0.58** |
| Persistent configuration volume | 1 GB × $0.10/month | **$0.10/month** |
| Optional Anycast IPv4 | $2/month, billed by the minute | **up to about $2 for a 30-day month** |

**One movie during a 30-day month, with the resources allocated for that entire month:** about **$0.68 without Anycast**, or **$2.68 with an allocated Anycast IPv4**, *under these example assumptions*. The $2 IP is **not a per-film fee**: if you watch more films in the same month, that recurring IP cost is shared. If the IP is held for only part of the month, billing is prorated.

**Not included:** additional outgoing BitTorrent peer uploads/seeding, repeat streaming or retries, any extra CDN/delivery charges applicable to your specific configuration, other regions' different bandwidth prices, taxes, other Bunny services, and account-level minimum charges. A 50 GB torrent file does **not** guarantee exactly 50 GB billed: the actual network traffic can be higher. Bunny prices may change. Check **your Bunny usage and billing dashboard** for the definitive amount.

**Official rates (checked 2 November 2026):** [Magic Containers — compute, storage, Anycast, bandwidth](https://bunny.net/magic-containers/) · [Bunny CDN pricing](https://bunny.net/pricing/cdn/).

## 6. Auto-stop after 60 idle minutes — easy guide

**How it works:** Start TorrServer, watch a movie in Lampa, and stop playback. If the gateway detects **no video transfer for 60 continuous minutes** and no active media request, GitHub Actions will try to stop your Bunny container. **This is not 60 minutes after starting the server** and not a guaranteed exact-time timer.

### Set up once

**1. Prepare GitHub.** Install [GitHub CLI (`gh`)](https://cli.github.com/), sign in with `gh auth login` if necessary, and use **your own fork of [TorrServer-bunny](https://github.com/vbrekher/TorrServer-bunny)**. Make sure your fork includes `.github/workflows/idle-watchdog.yml`. The original repository owner may use the original repository. **Never put your Bunny API key in somebody else's GitHub repository.**

**2. Update your Mac/Linux command-line app (does not create another server):**

```bash
curl -fsSL --retry 3 \
  https://raw.githubusercontent.com/vbrekher/TorrServer-bunny/master/install-bunny.sh \
  -o /tmp/torrserver-bunny-update.sh \
  && sh /tmp/torrserver-bunny-update.sh status
```

If your existing server is `inactive`, run `~/.local/bin/torrserver-bunny start` once and check `status` until `State: active`. **Do not repeat start while Bunny is `progressing` or after a timeout without checking status first.**

**3. Play a test video in Lampa for a minute. Then run:**

```bash
~/.local/bin/torrserver-bunny activity
```

Look for `Tracked media bytes since container startup` **greater than zero**. This proves that playback passes through the monitored gateway. If you see `0`, play a test video **since the last container start** and check again. **Do not enable auto-stop while the count is zero.** The optional `activity --probe` requires the updated Docker image on the live Bunny app.

**4. Connect automatic checks to your own GitHub account:**

```bash
# Replace YOUR_USERNAME with your own GitHub username.
REPO="YOUR_USERNAME/TorrServer-bunny"

gh auth status
~/.local/bin/torrserver-bunny enable-github-watchdog --repo "$REPO"
# Type ENABLE when asked; continue only after "Secrets installed".
gh workflow enable idle-watchdog.yml -R "$REPO"
gh workflow run idle-watchdog.yml -R "$REPO"
gh run list --workflow idle-watchdog.yml -R "$REPO" -L 5
```

When prompted, type `ENABLE`. The CLI installs four values into **GitHub Actions Secrets** of your repository. **Continue to the `gh workflow` commands only if you see `Secrets installed`**. If `gh auth status` fails, sign in using `gh auth login`. Never paste credentials into README files or issues.

### Everyday use

**Start:** `~/.local/bin/torrserver-bunny start`, then wait for `State: active` using `status`. Lampa cannot start an undeployed server by itself.

**Watch:** Use Lampa normally.

**Finish:** Stop playback, but leave the Bunny app running. After **at least 60 minutes without tracked video**, GitHub Actions (approximately every 10 minutes) can request `undeploy`. A new video stream resets the idle period. GitHub's schedule can run late or be skipped.

**Check whether it stopped:**

```bash
REPO="YOUR_USERNAME/TorrServer-bunny"
gh run list --workflow idle-watchdog.yml -R "$REPO" -L 10
~/.local/bin/torrserver-bunny status
```

Open GitHub → **Actions → Stop TorrServer after 60 minutes without media streaming**. `IDLE_STOP_REQUESTED` means a stop was **requested**, not necessarily completed; confirm `State: inactive` using `status`. A green GitHub Actions run alone does **not** prove the server stopped.

### Good to know

- **No streaming since startup?** The counter stays `0` and the safety rule will **not automatically stop** the container. Use `~/.local/bin/torrserver-bunny stop` instead.
- **Watching a movie:** recognized active media requests prevent stop; unmonitored streaming routes still need separate validation.
- **Your computer may be off:** GitHub Actions performs scheduled checks in the cloud after setup.
- **Costs:** stopping container compute does not necessarily stop persistent-storage or allocated Anycast IPv4 charges.
- **Security:** Bunny API keys have broad permissions. Keep your GitHub repo and its workflows secure.
- **Current verification:** Lampa playback is owner-confirmed; an actual successful 60-minute auto-stop is **not yet verified**.

## 7. Problems and quick fixes

| Symptom | What to do |
| --- | --- |
| `State: active`, but no film plays | Check the true HTTPS CDN address and credentials; test a lawful torrent; inspect Bunny container logs. Torrent peers and Samsung Tizen format support need separate real-world testing. |
| `https://IP:32000` is printed as the server URL | This is the **wrong Anycast peer endpoint**. Update your CLI and run `status` to refresh the HTTPS CDN URL. |
| The HTTPS domain is missing | Inspect the `torrserver-https` endpoint in Bunny Dashboard; check whether provisioning finished. Do not create another app. |
| `Already configured` | Good — the server exists locally. Use `status`, `start`, or `stop`; never repeat first-time `setup` casually. |
| `HTTP 500` when creating an app | **Do not repeat `CREATE` blindly.** Use `~/.local/bin/torrserver-bunny doctor`, inspect the Bunny dashboard and API limits, and contact Bunny Support if necessary. |
| `GHCR image` / registry error | Confirm the public image exists and your GHCR registry is configured; the CLI requires a valid **numeric Bunny registry ID**. |

For more detail on security and networking, see [deployment/technical notes](../bunny/README.md). To get the latest CLI version **without creating a new app**, run the installer with `status`:

```bash
curl -fsSL --retry 3 \
  https://raw.githubusercontent.com/vbrekher/TorrServer-bunny/master/install-bunny.sh \
  -o /tmp/install-torrserver-bunny.sh \
  && sh /tmp/install-torrserver-bunny.sh status
```

## Credits and legal use

TorrServer is originally developed by **[YouROK and contributors](https://github.com/YouROK/TorrServer)** — sincere thanks for making it open source. **TorrServer Bunny** adds a Magic Containers installation workflow, endpoint/auth setup, manual lifecycle control, and optional activity-aware shutdown. It does not host or supply copyrighted movies, torrents, or catalogs. You are responsible for complying with applicable laws and sharing rights. See [LICENSE](../LICENSE).
