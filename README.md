<div align="center">

<img src="docs/assets/torrserver-bunny-hero.svg" width="100%" alt="TorrServer Bunny — your server, your movie night. Illustrated start, connect and stop workflow." />

<br />

**A self-hosted TorrServer experience without renting a VPS.**  
Deploy on [bunny.net Magic Containers](https://bunny.net/magic-containers/), connect with Lampa, and control when the server runs.

<br />

<a href="https://github.com/vbrekher/TorrServer-bunny/actions/workflows/bunny-cli-tests.yml"><img alt="Tests" src="https://github.com/vbrekher/TorrServer-bunny/actions/workflows/bunny-cli-tests.yml/badge.svg" /></a>
<a href="LICENSE"><img alt="License GPL-3.0" src="https://img.shields.io/badge/license-GPL--3.0-786BF6?style=flat" /></a>
<img alt="Platforms: macOS and Linux" src="https://img.shields.io/badge/CLI-macOS%20%7C%20Linux-263556?style=flat" />
<img alt="Bunny Magic Containers" src="https://img.shields.io/badge/hosting-Bunny%20Magic%20Containers-FF7096?style=flat" />
<img alt="Samsung Tizen playback not yet verified" src="https://img.shields.io/badge/TV%20playback-testing-EFAE61?style=flat" />

<br /><br />

**[Quick start](#-get-started)** &nbsp;·&nbsp; **[Connect Lampa](#-connect-to-lampa)** &nbsp;·&nbsp; **[Pricing](#-what-does-a-50-gb-movie-cost)** &nbsp;·&nbsp; **[Documentation](#-documentation)**

</div>

---

## 🌍 Documentation

<div align="center">

| 🇷🇺 **Русский** | 🇬🇧 **English** | 🇳🇱 **Nederlands** |
| :---: | :---: | :---: |
| **[Руководство пользователя →](docs/README.ru.md)** | **[User guide →](docs/README.en.md)** | **[Gebruikershandleiding →](docs/README.nl.md)** |
| Установка · Lampa · Цены | Setup · Lampa · Pricing | Installatie · Lampa · Kosten |

</div>

## A personal streaming server, on your terms.

TorrServer Bunny is a deployment and control layer built around the open-source **[TorrServer by YouROK](https://github.com/YouROK/TorrServer)**. Instead of maintaining a 24/7 VPS, you use a container on Bunny, a private HTTPS CDN address, and three simple terminal commands to manage it.

<table>
<tr>
<td width="33%" valign="top">

### ☁️ No VPS to manage

Runs in **Bunny Magic Containers**. Select one region; the installer handles the container, credentials and HTTPS endpoint.

</td>
<td width="33%" valign="top">

### 📺 Built for Lampa

Copy the **HTTPS CDN domain** into Lampa's TorrServer settings. Your account gets its own login and generated password.

</td>
<td width="33%" valign="top">

### ⏻ Start & stop on demand

Stop compute after a film. Start the **same application** again later, with its persistent configuration intact.

</td>
</tr>
<tr>
<td width="33%" valign="top">

### 🔒 Access controlled

TorrServer login credentials are saved locally. The HTTPS endpoint uses authentication; the Bunny API key stays out of the container.

</td>
<td width="33%" valign="top">

### 🧩 Optional peer networking

Enable a separately billed **Anycast IPv4** endpoint for inbound BitTorrent TCP/UDP connections.

</td>
<td width="33%" valign="top">

### 🕒 Optional idle watchdog

A scheduled GitHub Action can request a stop after **60+ minutes** without media activity. Best effort, not a guaranteed timer.

</td>
</tr>
</table>

## 🚀 Get started

<sub>**FIRST-TIME SETUP · macOS / Linux · Python 3 + curl · Bunny account required**</sub>

**1. Open Terminal** on your Mac or Linux computer. Copy and run:

```bash
curl -fsSL --retry 3 \
  https://raw.githubusercontent.com/vbrekher/TorrServer-bunny/master/install-bunny.sh \
  -o /tmp/install-torrserver-bunny.sh \
  && sh /tmp/install-torrserver-bunny.sh
```

**2. Answer the guided setup questions.** The wizard will ask for your private Bunny account API key, region (for example `AMS` or `DE`), a username and whether you want the *optional paid* Anycast peer port. It generates a password automatically. Type **`CREATE` once** to approve billable resources.

**3. Get your private server address.** After provisioning, run `status` and look for the **HTTPS CDN URL**. A valid *example* looks like `https://mc-example.bunny.run`. Use **your own address**, not this example.

> [!IMPORTANT]
> Setup creates **paid Bunny resources**. If you already have an app, do **not** run the setup wizard again. Go straight to the daily commands below.

### Your everyday commands

<table>
<tr><th>Action</th><th>Command</th><th>What happens</th></tr>
<tr><td>🟢 <b>Start</b></td><td><code>~/.local/bin/torrserver-bunny start</code></td><td>Deploys your existing server</td></tr>
<tr><td>🔍 <b>Status</b></td><td><code>~/.local/bin/torrserver-bunny status</code></td><td>Checks Bunny status and HTTPS URL</td></tr>
<tr><td>🔴 <b>Stop</b></td><td><code>~/.local/bin/torrserver-bunny stop</code></td><td>Stops running containers, not the saved app</td></tr>
</table>

Starting and stopping are **asynchronous**. Wait for `active` in `status` before expecting the stream to work. Opening Lampa **will not** automatically start a stopped container.

## 📺 Connect to Lampa

<table>
<tr><td><b>1. Find the HTTPS URL</b></td><td>Run <code>~/.local/bin/torrserver-bunny status</code> and copy the line <code>TorrServer HTTPS CDN URL</code>.</td></tr>
<tr><td><b>2. Retrieve credentials privately</b></td><td>Run <code>~/.local/bin/torrserver-bunny status --show-credentials</code> on your own computer.</td></tr>
<tr><td><b>3. Configure Lampa</b></td><td>Open <b>Lampa → Settings → TorrServer</b> and enter the HTTPS CDN domain, username and password. Menu names may vary.</td></tr>
<tr><td><b>4. Try a test stream</b></td><td>Test with a torrent that you are allowed to download and share. TV codec and torrent peer compatibility require real testing.</td></tr>
</table>

> [!WARNING]
> **Do not use an Anycast IP ending in `:32000` as your Lampa server URL.** That is a BitTorrent peer port, not the HTTPS web endpoint. For Lampa, use the **HTTPS CDN domain** returned by `status`.

## 💸 What does a 50 GB movie cost?

An **illustrative Blu-ray-size movie** streamed over **3 hours** to one viewer in Europe / North America, assuming **one fully utilized CPU core** and **1 GB of billed RAM** for that period:

| Usage | Calculation | Example |
| :--- | ---: | ---: |
| 📡 50 GB outgoing video traffic | 50 × $0.01/GB | **$0.50** |
| ⚙️ CPU for 3 hours | 3 × $0.02/core-hour | **$0.06** |
| 🧠 RAM for 3 hours | 3 × $0.005/GB-hour | **$0.015** |
| **Estimated session subtotal** | **Network + assumed compute** | **≈ $0.58** |
| 💾 Persistent 1 GB configuration volume | Monthly allocation | **≈ $0.10 / month** |
| 🌐 Optional Anycast IPv4 | Full-month allocation | **≈ $2 / month** |

**One such movie in a 30-day month, with resources retained all month:**

| Configuration | Illustrative total |
| :--- | ---: |
| Without Anycast IP | **≈ $0.68 / month** |
| With an allocated Anycast IPv4 | **≈ $2.68 / month** |

<sub>**This is not a guaranteed bill.** The session estimate excludes BitTorrent peer upload / seeding (potentially significant), extra or repeated traffic, additional applicable CDN charges, region-specific prices, taxes, other Bunny products and account minimums. CPU and RAM usage are assumptions, not measurements. `stop` stops compute, but allocated storage and Anycast can remain billable. Bunny rates and billing may change. Rates referenced as of **2 November 2026**: [Magic Containers](https://bunny.net/magic-containers/) · [CDN pricing](https://bunny.net/pricing/cdn/).</sub>

## 🕒 Hands-free shutdown (optional)

The HTTP gateway records movie-stream activity without giving the running container your Bunny management API key. You can run a GitHub Actions watchdog in **a repository you own and trust**:

```bash
~/.local/bin/torrserver-bunny enable-github-watchdog --repo YOUR-ACCOUNT/YOUR-REPOSITORY
```

The workflow checks approximately every ten minutes and requests `undeploy` only after at least **60 minutes without media activity**. It requires GitHub CLI and the [included watchdog workflow](.github/workflows/idle-watchdog.yml). Enabling it stores Bunny credentials as **GitHub Actions secrets in your repository**. Review the workflow and repository access first.

**The schedule is best effort**; GitHub may delay or skip runs. It does not guarantee a precise billing cutoff, and it does not automatically start the server when Lampa opens.

<details>
<summary><strong>🔧 Advanced troubleshooting and useful commands</strong></summary>

<br />

| Situation | What to do |
| --- | --- |
| Already installed | Use `start`, `status` and `stop` — **not** `setup`. |
| Need your password | `~/.local/bin/torrserver-bunny status --show-credentials` (keep output private). |
| No HTTPS domain yet | Check `torrserver-https` under **Magic Containers → Endpoints** in Bunny. Do not create another app. |
| Wrong IP address appears | Update the CLI and run `status`; use the HTTPS CDN **domain**, not Anycast port `32000`. |
| Creation returned HTTP 500 | Do not retry `CREATE` blindly; run `~/.local/bin/torrserver-bunny doctor` and check your Bunny dashboard. |
| Update the CLI without creating a server | Run the installer with the `status` argument (see below). |

```bash
curl -fsSL --retry 3 \
  https://raw.githubusercontent.com/vbrekher/TorrServer-bunny/master/install-bunny.sh \
  -o /tmp/install-torrserver-bunny.sh \
  && sh /tmp/install-torrserver-bunny.sh status
```

More detail: **[Technical deployment guide](bunny/README.md)**.

</details>

## ✅ Project status

| Capability | Verification |
| --- | --- |
| Real Magic Containers app created | ✅ Confirmed from owner deployment on 2 November 2026 |
| Application `active`, HTTPS CDN URL received | ✅ Confirmed from Bunny API output |
| Python CLI and Go gateway | ✅ Automated tests in [GitHub Actions](https://github.com/vbrekher/TorrServer-bunny/actions/workflows/bunny-cli-tests.yml) |
| BitTorrent streaming through Lampa on physical Samsung Tizen | 🧪 Not yet verified |
| Scheduled 60-minute shutdown on live Bunny | 🧪 Not yet verified |

**Important distinction:** an active container and a working HTTPS endpoint do **not** prove successful TV playback. This project does not provide or distribute movies, catalogs or copyrighted material.

## ❤️ Built on open source

<div align="center">

**A big thank-you to [YouROK and all contributors to TorrServer](https://github.com/YouROK/TorrServer).**

TorrServer Bunny is an independent deployment and lifecycle layer built around their work. The original torrent engine, its upstream community and its license deserve clear recognition.

[Original TorrServer](https://github.com/YouROK/TorrServer) · [Lampa](https://github.com/yumata/lampa) · [Technical guide](bunny/README.md) · [GPL-3.0 License](LICENSE)

<sub>Use only content you are legally entitled to access and share. This repository does not host any films or torrent catalog.</sub>

</div>
