# TorrServer Bunny — eenvoudige handleiding (Nederlands)

[🇷🇺 Русский](README.ru.md) · [🇬🇧 English](README.en.md) · **🇳🇱 Nederlands** · [Projectpagina](../README.md)

Met **TorrServer Bunny** gebruik je de open-source [TorrServer van YouROK](https://github.com/YouROK/TorrServer) via [bunny.net Magic Containers](https://bunny.net/magic-containers/). Je hoeft geen eigen VPS te huren. De server kan samenwerken met Lampa en geschikte apparaten.

**Heel eenvoudig:** één keer installeren → het HTTPS-adres invoeren in Lampa → **start** vóór je een film bekijkt → **stop** als je klaar bent. Je instellingen blijven bewaard.

> **Wat al is bevestigd:** op **2 november 2026** is een echte Bunny-app aangemaakt. Bunny gaf de status `active` en een HTTPS CDN-adres terug. Het afspelen op een fysieke Samsung-tv met Tizen, verbindingen met torrentpeers en het automatisch uitschakelen zijn nog **niet** afzonderlijk in de praktijk getest. Niet elke torrent, Lampa-versie of videocodec hoeft te werken.

## 1. Wat heb je nodig?

- Een [bunny.net-account](https://dash.bunny.net/) met toegang tot **Magic Containers**, plus je geheime **Bunny account API key**.
- Een **Mac of Linux-computer** met `python3` en `curl`. Voor de gewone installatie heb je **geen Docker of VPS** nodig.
- Lampa op je tv of een ander compatibel apparaat, met een instelling voor TorrServer.
- Een internetverbinding en torrents die je legaal mag gebruiken en delen.

De openbare containerimage is `ghcr.io/vbrekher/torrserver-bunny:main`. Kan Bunny deze image niet via je GHCR-register controleren, dan stopt de installatie voordat er een betaalde app wordt aangemaakt.

## 2. Installeren — slechts één keer

Open **Terminal** op je Mac of Linux-computer. Kopieer de hele opdracht:

```bash
curl -fsSL --retry 3 \
  https://raw.githubusercontent.com/vbrekher/TorrServer-bunny/master/install-bunny.sh \
  -o /tmp/install-torrserver-bunny.sh \
  && sh /tmp/install-torrserver-bunny.sh
```

De installatie vraagt het volgende:

| Vraag | Wat vul je in? |
| --- | --- |
| **Bunny account API key** | Je persoonlijke Bunny API-sleutel. De invoer is verborgen. Deel deze sleutel nooit in een chat of screenshot. |
| **Select region** | Kies één regio, bijvoorbeeld `AMS` (Amsterdam) of `DE` (Duitsland). |
| **TorrServer username** | Druk op Enter voor `lampa`, of kies zelf een gebruikersnaam. |
| **Expose BitTorrent TCP/UDP peer port via Anycast?** | `N` voor een goedkopere eerste test zonder extra IP-adres; `y` voor een betaald IPv4-adres waarmee torrentpeers inkomende verbindingen kunnen maken. |
| **Confirm** | Typ **één keer** `CREATE` om toestemming te geven voor betaalde Bunny-resources. |

De installer maakt één Magic Containers-app in één regio aan, met **1 GB permanente opslag voor instellingen** en een **HTTPS CDN-eindpunt**. Kies je `y`, dan vraagt de installer apart een betaald Anycast IPv4-eindpunt aan. Het wachtwoord wordt automatisch gemaakt en **lokaal** in een beveiligd bestand bewaard.

**Heb je de server al geïnstalleerd?** Voer de eerste installatie dan **niet opnieuw** uit. Gebruik de opdrachten in stap 4.

## 3. Lampa verbinden

Controleer de serverstatus:

```bash
~/.local/bin/torrserver-bunny status
```

Zoek naar `State: active` en **`TorrServer HTTPS CDN URL:`**. Een geldig voorbeeld is `https://mc-example.bunny.run`. Dit is **alleen een voorbeeld**, niet jouw eigen serveradres.

Je wachtwoord kun je **privé op je eigen computer** bekijken met:

```bash
~/.local/bin/torrserver-bunny status --show-credentials
```

Open **Lampa → Instellingen → TorrServer** (de exacte menunamen kunnen per versie verschillen):

| Veld | In te vullen waarde |
| --- | --- |
| Server / URL | **Jouw HTTPS CDN-domein** uit `status` |
| Gebruikersnaam | Bijvoorbeeld `lampa`, of je eigen naam |
| Wachtwoord | Het wachtwoord uit de installer of `--show-credentials` |

**Gebruik niet het verkeerde adres.** Een adres zoals `https://203.0.113.10:32000` is **niet voor Lampa**. Poort `32000` is voor torrentpeers. Voor Lampa gebruik je het **HTTPS CDN-domein**, zonder `:32000`.

Ontbreekt het HTTPS-adres nog? Ga naar **Bunny Dashboard → Magic Containers → jouw app → Endpoints** en zoek `torrserver-https`. Je kunt het echte HTTPS-domein zelf opslaan:

```bash
~/.local/bin/torrserver-bunny set-url https://JOUW-ECHTE-CDN-DOMEIN
```

Controleer of het HTTPS-adres in je browser reageert. Probeer daarna een **legaal te verspreiden testtorrent** in Lampa. Alleen de status `active` bewijst nog niet dat afspelen op jouw Samsung-tv werkt.

## 4. Dagelijks gebruik: aanzetten en uitzetten

Je hoeft **niet opnieuw te installeren** als je een andere film wilt kijken.

| Wat wil je doen? | Opdracht in Terminal |
| --- | --- |
| Server **starten** vóór het kijken | `~/.local/bin/torrserver-bunny start` |
| Status en adres **controleren** | `~/.local/bin/torrserver-bunny status` |
| Server na afloop **stoppen** | `~/.local/bin/torrserver-bunny stop` |
| Wachtwoord privé **bekijken** | `~/.local/bin/torrserver-bunny status --show-credentials` |

`start` start **de bestaande app** opnieuw, `stop` stopt de actieve containers en `status` controleert de toestand. Opstarten gebeurt niet altijd direct: controleer met `status` of de app weer `active` is.

**Lampa kan een gestopte container niet automatisch opstarten.** Start de server eerst op je computer. `stop` verwijdert de app of je instellingen **niet** en het HTTPS-adres hoort behouden te blijven. Permanente opslag en een toegewezen Anycast-IP kunnen echter kosten blijven veroorzaken terwijl de container uitstaat.

## 5. Wat kost één Blu-ray-film van 50 GB?

Hieronder staat een **rekenvoorbeeld**, geen vaste prijs. Stel dat je met **één kijker** een volledige film van **50 GB** streamt naar **Europa of Noord-Amerika**, gedurende **3 uur**. We rekenen voor dit voorbeeld met **1 GB gefactureerd RAM** en **één CPU-core op volle belasting gedurende drie uur**. Het werkelijke gebruik kan afwijken.

| Kostenpost | Berekening | Geschatte kosten |
| --- | ---: | ---: |
| 50 GB uitgaand videoverkeer | 50 × $0,01/GB | **$0,50** |
| CPU (voorbeeld) | 3 uur × 1 core × $0,02 | **$0,06** |
| RAM (voorbeeld) | 3 uur × 1 GB × $0,005 | **$0,015** |
| **Voorbeeld voor één filmsessie** | **Dataverkeer + CPU + RAM** | **$0,575 ≈ $0,58** |
| Permanente opslag voor instellingen | 1 GB × $0,10/maand | **$0,10/maand** |
| Optioneel Anycast IPv4 | $2/maand, per minuut berekend | **ongeveer $2 per volledige maand** |

**Bekijk je in één maand maar één film van 50 GB**, en houd je de opslag en het Anycast-IP die hele maand toegewezen, dan is het rekenvoorbeeld:

- **Zonder Anycast:** $0,575 + $0,10 ≈ **$0,68 per maand**.
- **Met Anycast:** $0,575 + $0,10 + $2 ≈ **$2,68 per maand**.

**De $2 voor het IP-adres betaal je niet per film.** Het gaat om de prijs voor een volledige maand. Bij meerdere films in dezelfde maand deel je deze terugkerende kosten. Wordt het IP-adres slechts een deel van de maand toegewezen, dan is de berekening naar rato.

**Niet inbegrepen:** extra uitgaand verkeer naar torrentpeers (*seeding/upload*), opnieuw streamen of herhaalde downloads, eventuele aanvullende CDN-/afleverkosten afhankelijk van je configuratie, andere regio's, belastingen, andere Bunny-diensten en minimumkosten voor het account. Een torrentbestand van 50 GB betekent **niet automatisch** precies 50 GB gefactureerd verkeer. Controleer voor de definitieve kosten je Bunny-dashboard.

Officiële prijzen (gecontroleerd op **2 november 2026**): [Magic Containers](https://bunny.net/magic-containers/) · [Bunny CDN-prijzen](https://bunny.net/pricing/cdn/).

## 6. Optioneel: automatisch stoppen na 60 minuten

Standaard stop je de server zelf. Dit project bevat daarnaast een **GitHub Actions-watchdog**. Die controleert ongeveer elke 10 minuten of er videostreams actief zijn en vraagt om de server te stoppen wanneer er **minstens 60 minuten** geen videostreamactiviteit is.

Hiervoor heb je de ingelogde [GitHub CLI](https://cli.github.com/) (`gh`) nodig, plus **een eigen GitHub-repository of fork** met `.github/workflows/idle-watchdog.yml` en toestemming om Actions-secrets in te stellen.

```bash
~/.local/bin/torrserver-bunny enable-github-watchdog --repo JOUW-ACCOUNT/JOUW-REPOSITORY
```

Lees eerst het workflowbestand. Typ pas `ENABLE` als je de repository vertrouwt. De opdracht slaat onder andere je Bunny API-sleutel op als **GitHub Actions-secret in jouw eigen repository**. Plaats zo'n sleutel nooit in een repository van iemand anders.

**Let op:** geplande GitHub Actions kunnen vertraagd zijn of niet draaien. Automatisch stoppen en het beëindigen van kosten op precies 60 minuten zijn **niet gegarandeerd**. De watchdog start de server **niet** wanneer je Lampa opent.

## 7. Problemen oplossen

| Probleem | Oplossing |
| --- | --- |
| De app is `active`, maar de film speelt niet | Controleer je HTTPS CDN-adres en inloggegevens, probeer een legale testtorrent en bekijk de Bunny-containerlogs. Torrentpeers en Samsung-codecs moeten afzonderlijk worden getest. |
| Je ziet `https://IP:32000` als serveradres | Dit is het **verkeerde Anycast-peeradres**. Werk de CLI bij en voer `status` uit om het CDN-adres op te halen. |
| Er is geen HTTPS-adres | Zoek het eindpunt `torrserver-https` in het Bunny-dashboard. Maak **geen tweede app** aan. |
| `Already configured` | De installatie bestaat al. Gebruik `start`, `status` of `stop` in plaats van opnieuw `setup`. |
| `HTTP 500` bij het aanmaken | Probeer niet steeds opnieuw `CREATE`. Gebruik `~/.local/bin/torrserver-bunny doctor` en controleer het Bunny-dashboard; neem indien nodig contact op met Bunny Support. |
| Fout met GHCR of register | Controleer of de image openbaar is en of je Bunny GHCR-register een geldig **numeriek ID** heeft. |

**De CLI bijwerken zonder een nieuwe app aan te maken** kan zo:

```bash
curl -fsSL --retry 3 \
  https://raw.githubusercontent.com/vbrekher/TorrServer-bunny/master/install-bunny.sh \
  -o /tmp/install-torrserver-bunny.sh \
  && sh /tmp/install-torrserver-bunny.sh status
```

Meer technische informatie: [Handleiding voor beheer en beveiliging](../bunny/README.md).

## Dankwoord en legaal gebruik

**Hartelijk dank aan [YouROK en alle bijdragers aan TorrServer](https://github.com/YouROK/TorrServer)** voor het open-source project. TorrServer Bunny voegt een eenvoudige Bunny-installatie, HTTPS-verbinding, start-/stopbeheer en een optionele automatische stopfunctie toe. Deze repository levert **geen films, illegale torrentcatalogi of auteursrechtelijk beschermd materiaal**. Je bent zelf verantwoordelijk voor legaal gebruik en de rechten om bestanden te delen. Zie de [licentie](../LICENSE).
