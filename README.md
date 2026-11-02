# 🎬 TorrServer Bunny

### Your TorrServer, on Bunny Magic Containers. No VPS required.

A beginner-friendly way to run the original **[YouROK TorrServer](https://github.com/YouROK/TorrServer)** on **[bunny.net Magic Containers](https://bunny.net/magic-containers/)** and connect it to **[Lampa](https://github.com/yumata/lampa)** on a compatible TV or device.

**Install once. Start for a movie. Stop when you are done.**

### 📖 Choose your language / Выберите язык / Kies je taal

| 🇷🇺 Русский | 🇬🇧 English | 🇳🇱 Nederlands |
| --- | --- | --- |
| **[Полная инструкция](docs/README.ru.md)** | **[Complete user guide](docs/README.en.md)** | **[Volledige handleiding](docs/README.nl.md)** |
| Установка, Lampa, запуск, остановка, стоимость | Setup, Lampa, start/stop, pricing | Installeren, Lampa, starten/stoppen, kosten |

## ✨ What does it do?

- **No VPS:** deploy the container to one Bunny Magic Containers region.
- **Private access:** an HTTPS CDN endpoint with your own TorrServer username/password.
- **Manual on/off:** stop compute when you finish a film, and restart the **same** app later.
- **Saved configuration:** a 1 GB persistent volume retains server settings.
- **Optional BitTorrent connectivity:** add a separately billed Anycast IPv4 peer endpoint when needed.
- **Optional idle shutdown:** an external GitHub Actions watchdog can request a stop after at least 60 minutes without movie-stream activity.

The original **TorrServer engine belongs to YouROK and contributors**. This project adds Bunny deployment, endpoint/credential setup, lifecycle controls, and an HTTP activity gateway. **Thank you to the TorrServer creators and community!**

## 🚀 Quick start — first installation only

**Requirements:** a bunny.net account with Magic Containers enabled, a Bunny account API key, and a Mac/Linux computer with Python 3 and `curl`.

Open Terminal and run:

```bash
curl -fsSL --retry 3 \
  https://raw.githubusercontent.com/vbrekher/TorrServer-bunny/master/install-bunny.sh \
  -o /tmp/install-torrserver-bunny.sh \
  && sh /tmp/install-torrserver-bunny.sh
```

Follow the prompts: enter your Bunny key **privately**, choose a region, set a username, decide whether you want optional paid Anycast IPv4 for torrent peers, then type `CREATE` once to approve the billable resources.

**Already have a server? Do not run setup again.** Use the commands below.

## ▶️ Everyday use — three commands

| Action | Terminal command |
| --- | --- |
| **Start** the existing server | `~/.local/bin/torrserver-bunny start` |
| **Check** status and HTTPS URL | `~/.local/bin/torrserver-bunny status` |
| **Stop** compute after watching | `~/.local/bin/torrserver-bunny stop` |

Starting and stopping are **asynchronous**; check `status` until Bunny reports `active`. A stopped app does **not** automatically wake up when you open Lampa. `stop` keeps the app and settings; allocated storage and an Anycast IP (if any) can continue to cost money.

### 📺 Connect Lampa

1. Run `~/.local/bin/torrserver-bunny status` and copy **`TorrServer HTTPS CDN URL`** (a domain such as `https://mc-example.bunny.run`).
2. Run `~/.local/bin/torrserver-bunny status --show-credentials` **privately** to view your password.
3. In **Lampa → Settings → TorrServer**, enter your HTTPS CDN URL, username and password. Try a lawfully distributable test torrent.

**Do not use an Anycast IP with `:32000` as the Lampa address.** That port is for BitTorrent peers, not for HTTP playback. See the [English](docs/README.en.md), [Russian](docs/README.ru.md) or [Dutch](docs/README.nl.md) guide for screenshots-free step-by-step instructions and troubleshooting.

## 💰 Example: how much for one 50 GB Blu-ray-size film?

At Bunny's published Europe/North America network rate, **50 GB of outbound video data costs $0.50**. Assume a **3-hour session**, **one fully-used CPU core** and **1 GB of billed RAM**:

| Item | Example cost |
| --- | ---: |
| 50 GB outgoing data × $0.01/GB | **$0.50** |
| 3 hours CPU × 1 core × $0.02/core-hour | **$0.06** |
| 3 hours RAM × 1 GB × $0.005/GB-hour | **$0.015** |
| **Illustrative movie-session subtotal** | **$0.575 ≈ $0.58** |
| Persistent 1 GB configuration volume | **$0.10 per month** |
| Optional Anycast IPv4 | **$2 per full month** (prorated by minute) |

If you watch **one such film in a month** and keep those allocated resources for all 30 days, the example works out to **about $0.68 without Anycast** or **about $2.68 with Anycast**. This is **not a fixed bill**: actual CPU/RAM use, additional torrent peer upload/seeding, repeated data, any applicable CDN charges, region, taxes and other Bunny products or account minimums can change the result. An allocated Anycast IP may remain billable when the container is stopped.

Rates checked **2 November 2026**: [Bunny Magic Containers pricing](https://bunny.net/magic-containers/) · [Bunny CDN pricing](https://bunny.net/pricing/cdn/). Full assumptions and examples are explained in all three language guides.

## 🕒 Optional 60-minute idle stop

The built-in HTTP gateway records media activity. You can optionally add a **scheduled GitHub Actions watchdog** in a repository **you control** to request `undeploy` when there has been no movie-stream activity for at least 60 minutes.

```bash
~/.local/bin/torrserver-bunny enable-github-watchdog --repo YOUR-ACCOUNT/YOUR-REPOSITORY
```

Requires the [GitHub CLI](https://cli.github.com/) and `.github/workflows/idle-watchdog.yml` on your own repository's default branch. Review the workflow before entering `ENABLE`: this action stores your **Bunny account API key** in that repository's GitHub Actions secrets. GitHub scheduled runs are **best effort** and can be delayed or disabled, so this is **not** a guaranteed shutdown or billing cutoff.

## ✅ Verification status

| Area | Status |
| --- | --- |
| Real Magic Containers app creation in Bunny | **Confirmed** on 2 Nov 2026 |
| Bunny reported an `active` application and HTTPS CDN domain | **Confirmed** |
| GitHub Actions unit tests for CLI and Go gateway | **Passing** in latest verified CI |
| Real torrent playback on Samsung Tizen / Lampa | **Not yet verified** |
| Real scheduled 60-minute shutdown on Bunny | **Not yet verified** |

The existing source includes GitHub Actions checks for Python CLI and Go gateway; local mocks and a Bunny `active` state cannot substitute for a physical-TV playback test.

## 🔐 Safety and technical details

API keys stay in a restricted local configuration file except when **you explicitly opt in** to storing them as GitHub Actions secrets for the idle watchdog. Keep your Lampa password private, do not publish credentials in screenshots, and do not grant strangers access to the repository that holds account-level secrets.

- **Technical deployment and troubleshooting:** [bunny/README.md](bunny/README.md).
- **TorrServer upstream:** [YouROK/TorrServer](https://github.com/YouROK/TorrServer).
- **Lampa upstream:** [yumata/lampa](https://github.com/yumata/lampa).
- **License:** [GPL-3.0](LICENSE). No films, torrent catalogs or copyrighted media are distributed by this repository. Use the software only with content you are entitled to access and share.

---

**Made possible by the work of YouROK and the open-source TorrServer community. Thank you!**
