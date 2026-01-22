# Hetzner Automation

[English](README.md) | [中文](README_CN.md)

Automated monitoring and recovery for Hetzner servers with optional Cloudflare DNS updates and Telegram notifications.

## Features

- Monitor bandwidth usage and take action when thresholds are exceeded
- Delete/rebuild servers using snapshots
- Update Cloudflare DNS records after rebuild
- Telegram notifications for warnings and actions
- Runs as a systemd service

## Requirements

- Ubuntu/Debian with `python3`, `pip`, and `git`
- Root access (or `sudo`)

## Quick install

```bash
curl -fsSL https://raw.githubusercontent.com/liuweiqiang0523/Hetzner-Web/main/automation/install_hetzner_monitor.sh | sudo bash
```

What the one-line script does (for beginners):
1. Creates the install directory (default `/opt/hetzner-web`).
2. Clones the repo into that directory.
3. Sets up the Python environment and installs dependencies.
4. Generates/copies default config files (you still need to fill in tokens/credentials).
5. Installs and starts the `hetzner-monitor.service`.

Beginner step-by-step (what to fill):
1. Run the one-line command (no input needed).
2. Edit `/opt/hetzner-web/automation/config.yaml`: set `hetzner.api_token` (required), then fill Telegram/Cloudflare/Snapshot map if used.
3. Restart the service: `sudo systemctl restart hetzner-monitor.service`.

Default install dir: `/opt/hetzner-web` (override by passing a path to the script).

Short URL (optional):

```bash
curl -fsSL https://oknm.de/hz | bash
```

Note: ensure the short URL points to `https://raw.githubusercontent.com/liuweiqiang0523/Hetzner-Web/main/automation/install_hetzner_monitor.sh`.

## One-line install with auto-config (optional)

```bash
HETZNER_API_TOKEN="xxx" \
TELEGRAM_BOT_TOKEN="xxx" \
TELEGRAM_CHAT_ID="123" \
CF_API_TOKEN="xxx" \
CF_ZONE_ID="xxx" \
CF_RECORD_MAP="123456=server-a.example.com,789012=server-b.example.com" \
SNAPSHOT_MAP="123456=100200300,789012=100200301" \
LOCATION="nbg1" \
curl -fsSL https://raw.githubusercontent.com/liuweiqiang0523/Hetzner-Web/main/automation/install_hetzner_monitor.sh | sudo bash
```

Supported variables:

- `HETZNER_API_TOKEN` (required for auto-config)
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (optional)
- `CF_API_TOKEN`, `CF_ZONE_ID`, `CF_RECORD_MAP` (optional)
- `SNAPSHOT_MAP` (optional, server_id -> snapshot_id)
- `LOCATION`, `SERVER_TYPE`, `LIMIT_GB`, `CHECK_INTERVAL`, `EXCEED_ACTION`

`EXCEED_ACTION` supports: `notify`, `shutdown`, `delete`, `rebuild`, `delete_rebuild`.

## Service management

```bash
sudo systemctl status hetzner-monitor.service
sudo systemctl restart hetzner-monitor.service
sudo journalctl -u hetzner-monitor.service -f
```

## Configuration

After install, edit:

```bash
sudo nano /opt/hetzner-web/automation/config.yaml
```

Key sections:

- `hetzner.api_token`: Hetzner API token
- `traffic.limit_gb`: traffic limit in GB
- `traffic.check_interval`: minutes between checks
- `traffic.exceed_action`: `notify`, `shutdown`, `delete`, `rebuild`, `delete_rebuild`
- `traffic.confirm_before_delete`: require confirmation before destructive actions
- `telegram.enabled`, `telegram.bot_token`, `telegram.chat_id`
- `cloudflare.api_token`, `cloudflare.zone_id`
- `cloudflare.record_map`: server_id -> hostname
- `scheduler.enabled`: enable scheduled tasks
- `whitelist.server_ids` / `whitelist.server_names`: skip protected servers
- `server_template.server_type`, `server_template.location`
- `snapshot_map`: server_id -> snapshot_id

Full template: `config.example.yaml`.

Example maps:

```yaml
cloudflare:
  record_map:
    "123456": "server-a.example.com"
    "789012": "server-b.example.com"

snapshot_map:
  123456: 100200300
  789012: 100200301
```

## Telegram setup (detailed)

1) Create a bot with `@BotFather`, then copy the bot token.
2) Start a chat with your bot and send any message.
3) Get your chat ID:

```bash
curl -s "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates" | sed -n '1,200p'
```

4) Fill in:

```yaml
telegram:
  enabled: true
  bot_token: "YOUR_BOT_TOKEN"
  chat_id: "YOUR_CHAT_ID"
```

## Cloudflare setup (detailed)

1) Create an API token:
   - Cloudflare Dashboard → My Profile → API Tokens → Create Token
   - Use "Edit zone DNS" template, restrict to the target zone
2) Find your Zone ID:
   - Cloudflare Dashboard → your domain → Overview → Zone ID
3) Map server ID to DNS name:

```yaml
cloudflare:
  api_token: "YOUR_CF_TOKEN"
  zone_id: "YOUR_ZONE_ID"
  record_map:
    "123456": "server-a.example.com"
    "789012": "server-b.example.com"
```

The tool will update the A record for the mapped hostname after rebuild.

## Troubleshooting

- venv error on Debian/Ubuntu:
  ```bash
  sudo apt update
  sudo apt install -y python3-venv
  ```
- Cloudflare API token should have DNS edit permission for the target zone
- Telegram chat ID can be obtained by sending a message to your bot and checking updates

## Releases

This repo uses shared release tags for both Web and Automation. See `RELEASE_NOTES.md` at the repo root.

If you prefer versioned releases, you can tag a release on GitHub and install from it:

```bash
curl -fsSL https://raw.githubusercontent.com/liuweiqiang0523/Hetzner-Web/<TAG>/automation/install_hetzner_monitor.sh | sudo bash
```

This is optional. The default command always uses the latest `main`.
Release notes live in `RELEASE_NOTES.md`.

## Security note

This script pulls code from GitHub and runs it as root. Review the repository before use.
