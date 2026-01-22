![Hetzner-Web](docs/brand-logo.svg)

[English](README.md) | [中文](README.zh.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED)](#quick-start)

A lightweight Hetzner traffic dashboard + automation monitor. Includes a web UI, Telegram alerts/commands, auto rebuilds, and DNS checks.

## Table of Contents

- [Quick Start](#quick-start)
- [Screenshots](#screenshots)
- [Highlights](#highlights)
- [Use Cases](#use-cases)
- [Install Options](#install-options)
- [Prerequisites](#prerequisites)
- [Config Setup](#config-setup)
- [Telegram Setup](#telegram-setup)
- [Config File Locations](#config-file-locations)
- [Troubleshooting](#troubleshooting)
- [Project Layout](#project-layout)
- [Features](#features-list)
- [FAQ](#faq)
- [Security Notes](#security-notes)

---

<a id="quick-start"></a>
## ![Start](docs/icon-start.svg) Quick Start

If this is your first time, use the all-in-one script to install Web + automation + Telegram support in one go.

```bash
curl -fsSL https://raw.githubusercontent.com/liuweiqiang0523/Hetzner-Web/main/scripts/install-all.sh | sudo bash
```

Then continue with **Config Setup** below.

![Quick Start Flow](docs/quickstart-flow.light.svg)

---

<a id="screenshots"></a>
## ![Camera](docs/icon-camera.svg) Screenshots

![Web Dashboard](docs/web.png)
![Telegram Bot](docs/telegram.png)

---

<a id="highlights"></a>
## ![List](docs/icon-list.svg) Highlights

![Feature Cards](docs/feature-cards.svg)

---

<a id="use-cases"></a>
## ![List](docs/icon-list.svg) Use Cases

![Use Cases](docs/use-cases.svg)

Short and practical: this is built for bandwidth caps, night-time ops, and fast actions from Telegram.
Use it when you want visibility first, automation second, and manual control always nearby.

---

<a id="install-options"></a>
## ![Install](docs/icon-install.svg) Install Options

- All-in-one (recommended): `scripts/install-all.sh`
- Web-only: `scripts/install-docker.sh`
- Automation-only: `automation/install_hetzner_monitor.sh`

Existing deployments are safe by default. The all-in-one script exits if the install dir exists. If you really want to update an existing install:

```bash
curl -fsSL https://raw.githubusercontent.com/liuweiqiang0523/Hetzner-Web/main/scripts/install-all.sh | sudo ALLOW_UPDATE=1 bash
```

---

<a id="prerequisites"></a>
## ![Check](docs/icon-check.svg) Prerequisites

Make sure these commands exist:

```bash
git --version
python3 --version
docker --version
docker compose version
systemctl --version
```

If any are missing, install them first (Ubuntu/Debian: `apt`).

---

<a id="config-setup"></a>
## ![Config](docs/icon-config.svg) Config Setup

**Web config**
- `config.yaml`: set `hetzner.api_token`
- `web_config.json`: set `username` / `password`

**Automation config**
- `automation/config.yaml`: set Hetzner/Telegram/Cloudflare if needed

Apply changes:

```bash
cd /opt/hetzner-web

docker compose up -d --build
sudo systemctl restart hetzner-monitor.service
```

Open: `http://<your-server-ip>:1227`

---

<a id="telegram-setup"></a>
## ![Telegram](docs/icon-telegram.svg) Telegram Setup

In `automation/config.yaml`:

```yaml
telegram:
  enabled: true
  bot_token: "YOUR_BOT_TOKEN"
  chat_id: "YOUR_CHAT_ID"
```

Then restart automation:

```bash
sudo systemctl restart hetzner-monitor.service
```

---

<a id="config-file-locations"></a>
## ![Map](docs/icon-map.svg) Config File Locations

![Config Files](docs/config-files.light.svg)

- Web: `/opt/hetzner-web/config.yaml`
- Web login: `/opt/hetzner-web/web_config.json`
- Automation: `/opt/hetzner-web/automation/config.yaml`

---

<a id="troubleshooting"></a>
## ![Tools](docs/icon-tools.svg) Troubleshooting

![Troubleshooting Flow](docs/troubleshooting-flow.light.svg)

Quick checks:
- `docker ps`
- `sudo systemctl status hetzner-monitor.service`
- `sudo journalctl -u hetzner-monitor.service -n 50 --no-pager`

---

<a id="project-layout"></a>
## ![Layout](docs/icon-layout.svg) Project Layout

- Web dashboard (this directory): FastAPI + Vue, Docker-first
- Automation monitor: `automation/` (CLI/systemd service)

More docs:
- Automation docs: `automation/README.md`

---

<a id="features-list"></a>
## ![List](docs/icon-list.svg) Features

![Feature List](docs/feature-list-cards.svg)
If the image does not render, open `docs/feature-list-cards.svg` directly.

---

<a id="faq"></a>
## ![List](docs/icon-list.svg) FAQ

Q: The dashboard doesn't open. What should I check first?  
A: Make sure port `1227` is open and confirm containers are running with `docker ps`.

Q: Telegram messages are not arriving.  
A: Verify `bot_token` and `chat_id` in `automation/config.yaml`, then restart the service.

Q: I edited configs but nothing changed.  
A: Rebuild web with `docker compose up -d --build` and restart automation with `systemctl restart`.

Q: Where are my config files stored?  
A: Web configs live in `/opt/hetzner-web/` and automation config is in `/opt/hetzner-web/automation/`.

Q: Which install should I choose?  
A: Most users should pick the all-in-one script; only choose web-only or automation-only if you know you need just one.

Q: Can I re-run the install script safely?  
A: The all-in-one script exits if the install dir exists unless you set `ALLOW_UPDATE=1`.

---

<a id="security-notes"></a>
## ![Shield](docs/icon-shield.svg) Security Notes

- `config.yaml` / `web_config.json` / `automation/config.yaml` are sensitive. Do not commit them.
- Use HTTPS reverse proxy for public access.
