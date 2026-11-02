# TorrServer Bunny — Easy user guide (English)

[🇷🇺 Русский](README.ru.md) · **🇬🇧 English** · [🇳🇱 Nederlands](README.nl.md) · [Project home](../README.md)

Turn your [bunny.net Magic Containers](https://bunny.net/magic-containers/) account into a private [TorrServer](https://github.com/YouROK/TorrServer) for [Lampa](https://github.com/yumata/lampa) and compatible devices, without renting a VPS.

**In short:** install once on a Mac or Linux computer → enter the HTTPS server address in Lampa → run **start** when you want to watch → run **stop** afterwards. Your server and settings remain saved.

> **Current verification:** a real Bunny app was successfully created, and Bunny reported it **active** with an HTTPS CDN endpoint on 2 November 2026. Playback on a physical Samsung Tizen TV, peer connections, and the automatic idle-stop workflow have **not** been verified yet. This guide does not promise that all torrents, Lampa builds, or TV video formats work.

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

**Important:** a link such as `https://109.224.231.152:32000` is **not** the Lampa URL. Port `32000` is for BitTorrent peers, not the web player. Always use the HTTPS **CDN domain**.

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

## 6. Optional: automatic stop after an hour without streaming

By default you stop manually. The project also includes a **GitHub Actions watchdog** that checks streaming activity roughly every 10 minutes and requests a stop after at least **60 minutes without media streaming**.

This is **optional**. You need GitHub CLI (`gh`) authenticated on your computer, a GitHub repository **you control** containing this project's `.github/workflows/idle-watchdog.yml`, and permission to set GitHub Actions secrets.

```bash
~/.local/bin/torrserver-bunny enable-github-watchdog --repo YOUR-ACCOUNT/YOUR-REPOSITORY
```

Review the workflow and enter `ENABLE` if you trust that repository. This stores the Bunny API key and other runtime credentials as **GitHub Actions secrets in that repository**. Do not install account-level secrets into someone else's repository. A scheduled GitHub Action is **best effort** and can be delayed or disabled: it is **not** a guaranteed billing cutoff. It does **not** start the server automatically when Lampa opens.

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
