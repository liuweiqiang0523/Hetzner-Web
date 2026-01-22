![Hetzner-Web](docs/brand-logo.svg)

[English](README.md) | [中文](README.zh.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED)](#quick-start)

A lightweight Hetzner traffic dashboard + automation monitor. Includes a web UI, Telegram alerts/commands, auto rebuilds, and DNS checks.

---

<table>
  <tr>
    <td width="60%" valign="top">
      <strong>Start here</strong><br />
      One command installs Web + automation + Telegram support.<br /><br />
      <code>curl -fsSL https://raw.githubusercontent.com/liuweiqiang0523/Hetzner-Web/main/scripts/install-all.sh | sudo bash</code>
    </td>
    <td width="40%" valign="top">
      <strong>Next step</strong><br />
      Fill configs and restart services.<br /><br />
      <code>config.yaml</code> · <code>web_config.json</code> · <code>automation/config.yaml</code>
    </td>
  </tr>
</table>

---

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
- [Features](#features)
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

<a id="features"></a>
## ![List](docs/icon-list.svg) Features

![Feature List](docs/feature-list-cards.svg)

---

<a id="security-notes"></a>
## ![Shield](docs/icon-shield.svg) Security Notes

- `config.yaml` / `web_config.json` / `automation/config.yaml` are sensitive. Do not commit them.
- Use HTTPS reverse proxy for public access.
