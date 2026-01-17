# Hetzner Web

[English](README.md) | [中文](README.zh.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED)](#quick-start-docker)

A lightweight Hetzner traffic console with daily/hourly views, rebuild actions, DNS checks, and a clean dashboard.

## About

Hetzner Web is a focused control room for traffic visibility on Hetzner Cloud. It turns raw traffic data into daily and
hourly insights, highlights cap risk, and keeps rebuild/DNS actions close to the charts so you can react fast.

## Navigation

- Web dashboard quick install:
  `curl -fsSL https://raw.githubusercontent.com/liuweiqiang0523/Hetzner-Web/main/scripts/install-docker.sh | bash`
- Automation monitor quick install:
  `curl -fsSL https://raw.githubusercontent.com/liuweiqiang0523/Hetzner-Web/main/automation/install_hetzner_monitor.sh | sudo bash`
- Automation docs: `automation/README.md`

## Screenshot

<img width="2884" height="3973" alt="SCR-20260118-dyza" src="https://github.com/user-attachments/assets/b3e38d94-b655-46f0-998e-1aef311fcac9" />


## Features

- Real-time server traffic (outbound/inbound)
- Daily/hourly breakdown tables + daily per-server bars
- DNS check/sync + rebuild actions
- Telegram bot for query + control commands
- Snapshot rebuild + create from snapshot
- Scheduler for timed delete/create
- Trend sparkline per server
- Basic Auth login

## Project Layout

- Web dashboard (this directory): FastAPI + Vue, Docker-first.
- Automation monitor: `automation/` (CLI/systemd service).

Quick links:
- Web docs: `README.md` (this file)
- Automation docs: `automation/README.md`
- Automation install script: `automation/install_hetzner_monitor.sh`

## How It Works

- Fetches server + traffic data from the Hetzner Cloud API on refresh.
- Aggregates raw numbers into daily/hourly series and caches a rolling state in `report_state.json`.
- Serves a static Vue dashboard that renders charts client-side via `/api/*` endpoints.

## Tech Stack

- Backend: FastAPI + Python
- Frontend: Vue 3 (CDN) + vanilla JS/CSS

## Quick Start (Docker)

```bash
cp config.example.yaml config.yaml
cp web_config.example.json web_config.json
cp report_state.example.json report_state.json
# edit config.yaml + web_config.json

docker compose up -d --build
```

Open: `http://<server-ip>:1227`

## One-line Install (Docker)

```bash
curl -fsSL https://raw.githubusercontent.com/liuweiqiang0523/Hetzner-Web/main/scripts/install-docker.sh | bash
```

Optional env vars:
- `INSTALL_DIR`: install directory (default `/opt/hetzner-web`)
- `BRANCH`: git branch (default `main`)
- `REPO_URL`: repo URL

Example:

```bash
curl -fsSL https://raw.githubusercontent.com/liuweiqiang0523/Hetzner-Web/main/scripts/install-docker.sh | INSTALL_DIR=/srv/hetzner-web bash
```

## Automation (CLI/Systemd)

The original Hetzner automation monitor is now bundled in this repo under `automation/`.

- Entry point: `automation/main.py`
- Install docs: `automation/INSTALL.md` (English), `automation/INSTALL_CN.md` (中文)
- One-line install (from this repo): `automation/install_hetzner_monitor.sh`

This keeps the web dashboard and the automation service in one repository while remaining independently runnable.

## Reverse Proxy (Nginx example)

```nginx
server {
  listen 443 ssl;
  server_name hz.example.com;

  ssl_certificate /path/to/fullchain.pem;
  ssl_certificate_key /path/to/privkey.pem;

  location / {
    proxy_pass http://127.0.0.1:1227;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
```

## Configuration

### `config.yaml`
- `hetzner.api_token`: Hetzner Cloud API token
- `traffic.limit_gb`: traffic limit (GB)
- `traffic.check_interval`: polling interval (minutes)
- `traffic.exceed_action`: action on limit exceed (`rebuild` or empty)
- `scheduler.enabled`: enable scheduled tasks
- `scheduler.delete_time`: delete times (HH:MM, comma-separated)
- `scheduler.create_time`: create times (HH:MM, comma-separated)
- `telegram.bot_token`: Telegram bot token
- `telegram.chat_id`: Telegram chat ID
- `telegram.notify_levels`: alert thresholds (percent)
- `telegram.daily_report_time`: daily report time (HH:MM)
- `cloudflare.api_token`: Cloudflare API token
- `cloudflare.zone_id`: Cloudflare Zone ID
- `cloudflare.sync_on_start`: sync DNS on startup
- `cloudflare.record_map`: server_id or server_name -> DNS record
- `rebuild.snapshot_id_map`: server_id -> snapshot_id
- `rebuild.fallback_template`: fallback server template for rebuild

### `web_config.json`
- `username` / `password`: Basic Auth credentials
- `tracking_start`: optional, e.g. `2026-01-01 00:00`

## Telegram Commands

Query:
- `/list`: server list
- `/status`: system status
- `/traffic ID`: traffic details (all if no ID)
- `/today ID`: today traffic (all if no ID)
- `/report`: manual traffic report
- `/reportstatus`: last report time
- `/reportreset`: reset report window
- `/dnstest ID`: test DNS update
- `/dnscheck ID`: check DNS resolve

Control:
- `/startserver <ID>`: start server
- `/stopserver <ID>`: stop server
- `/reboot <ID>`: reboot server
- `/delete <ID> confirm`: delete server
- `/rebuild <ID>`: rebuild server

Snapshots:
- `/snapshots`: list snapshots
- `/createsnapshot <ID>`: create snapshot
- `/createfromsnapshot <SNAP_ID>`: create server from snapshot
- `/createfromsnapshots`: create servers from mapped snapshots

Schedule:
- `/scheduleon`: enable schedule
- `/scheduleoff`: disable schedule
- `/schedulestatus`: show schedule
- `/scheduleset delete=23:50,01:00 create=08:00,09:00`: set schedule

DNS:
- `/dnsync`: sync Cloudflare DNS

> `cloudflare.record_map` can be an object: `{ record, zone_id, api_token }` for per-server zones.

## Security Notes

- Keep `config.yaml` and `web_config.json` private (they are gitignored).
- Use HTTPS behind a reverse proxy.
- Consider IP allowlisting for the panel.

## Notes

- Runtime data is stored in `report_state.json` (gitignored).
- `config.yaml` and `web_config.json` are gitignored for safety.

## Releases

Repo-wide release notes live in `RELEASE_NOTES.md` and apply to both the Web dashboard and Automation monitor.

## License

MIT
