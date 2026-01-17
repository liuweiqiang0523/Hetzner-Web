# Hetzner Web

[English](README.md) | [中文](README.zh.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED)](#quick-start-docker)

A lightweight Hetzner traffic console with daily/hourly views, rebuild actions, DNS checks, and a clean dashboard.

## About

Hetzner Web is a focused control room for traffic visibility on Hetzner Cloud. It turns raw traffic data into daily and
hourly insights, highlights cap risk, and keeps rebuild/DNS actions close to the charts so you can react fast.

## Screenshot

![Dashboard](docs/screenshot.png)

## Features

- Real-time server traffic (outbound/inbound)
- Daily/hourly breakdown tables
- DNS check + rebuild actions
- Trend sparkline per server
- Traffic bar chart (outbound/inbound)
- Basic Auth login

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
- `cloudflare.record_map`: server_id -> DNS record
- `rebuild.snapshot_id_map`: server_id -> snapshot_id

### `web_config.json`
- `username` / `password`: Basic Auth credentials
- `tracking_start`: optional, e.g. `2026-01-01 00:00`

## Security Notes

- Keep `config.yaml` and `web_config.json` private (they are gitignored).
- Use HTTPS behind a reverse proxy.
- Consider IP allowlisting for the panel.

## Notes

- Runtime data is stored in `report_state.json` (gitignored).
- `config.yaml` and `web_config.json` are gitignored for safety.

## License

MIT
