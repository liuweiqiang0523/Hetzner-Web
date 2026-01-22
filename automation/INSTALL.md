# Installation (One-Command Script)

[English](INSTALL.md) | [中文](INSTALL_CN.md)

## Prerequisites
- Ubuntu/Debian with `python3`, `pip`, and `git`
- Root access (or `sudo`)

## Steps
1) Copy this repo to the target machine.
2) Run:

```bash
sudo ./install.sh
```

### One-line install (optional)
```bash
curl -fsSL https://raw.githubusercontent.com/liuweiqiang0523/Hetzner-Web/main/automation/install_hetzner_monitor.sh | sudo bash
```

What the one-line script does (for beginners):
1. Creates the install directory (default `/opt/hetzner-web`).
2. Clones the repo into that directory.
3. Sets up the Python environment and installs dependencies.
4. Generates/copies default config files (you still need to fill in tokens/credentials).
5. Installs and starts the `hetzner-monitor.service`.

Default install dir: `/opt/hetzner-web` (override by passing a path to the script).

### Short URL install (optional)
```bash
curl -fsSL https://oknm.de/hz | bash
```

Note: ensure the short URL points to `https://raw.githubusercontent.com/liuweiqiang0523/Hetzner-Web/main/automation/install_hetzner_monitor.sh`.

### One-line install with auto-config (optional)
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

3) Edit the config:

```bash
sudo nano /opt/hetzner-web/automation/config.yaml
```

Fill in:
- Hetzner API token
- Telegram bot token + chat ID
- Cloudflare API token + Zone ID + record map
- Snapshot map (server ID -> snapshot ID)

4) Restart service:

```bash
sudo systemctl restart hetzner-monitor.service
```

## Service
```bash
sudo systemctl status hetzner-monitor.service
sudo journalctl -u hetzner-monitor.service -f
```

## Troubleshooting

- venv error on Debian/Ubuntu:
  ```bash
  sudo apt update
  sudo apt install -y python3-venv
  ```

## Security note

This script pulls code from GitHub and runs it as root. Review the repository before use.
