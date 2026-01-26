#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Please run as root (sudo)." >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/venv"
SERVICE_FILE="/etc/systemd/system/hetzner-web.service"

if [[ ! -f "${ROOT_DIR}/config.yaml" ]]; then
  if [[ -f "${ROOT_DIR}/config.example.yaml" ]]; then
    cp "${ROOT_DIR}/config.example.yaml" "${ROOT_DIR}/config.yaml"
    echo "Created ${ROOT_DIR}/config.yaml from config.example.yaml"
  else
    echo "Missing config.example.yaml; please create config.yaml manually." >&2
    exit 1
  fi
else
  echo "Config exists: ${ROOT_DIR}/config.yaml"
fi

if [[ ! -d "${VENV_DIR}" ]]; then
  python3 -m venv "${VENV_DIR}"
fi

"${VENV_DIR}/bin/pip" install -r "${ROOT_DIR}/requirements.txt"
"${VENV_DIR}/bin/pip" install schedule

cat > "${SERVICE_FILE}" <<EOF
[Unit]
Description=Hetzner Monitor (traffic + auto rebuild)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=${ROOT_DIR}
ExecStart=${VENV_DIR}/bin/python ${ROOT_DIR}/main.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now hetzner-web.service

echo "Installed and started: hetzner-web.service"
echo "Edit ${ROOT_DIR}/config.yaml with your API tokens and settings."
