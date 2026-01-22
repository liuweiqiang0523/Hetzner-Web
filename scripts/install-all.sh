#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/liuweiqiang0523/Hetzner-Web.git}"
BRANCH="${BRANCH:-main}"
INSTALL_DIR="${INSTALL_DIR:-/opt/hetzner-web}"
ALLOW_UPDATE="${ALLOW_UPDATE:-0}"
FORCE_CONFIG="${FORCE_CONFIG:-0}"

info() {
  printf '[install-all] %s\n' "$1"
}

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf 'Missing command: %s\n' "$1" >&2
    exit 1
  fi
}

if [[ "${EUID}" -ne 0 ]]; then
  echo "Please run as root (sudo)." >&2
  exit 1
fi

need_cmd git
need_cmd docker
need_cmd python3
need_cmd systemctl

if docker compose version >/dev/null 2>&1; then
  COMPOSE='docker compose'
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE='docker-compose'
else
  printf 'Missing docker compose plugin (docker compose) or docker-compose\n' >&2
  exit 1
fi

if [ ! -d "$INSTALL_DIR" ]; then
  info "Cloning to $INSTALL_DIR"
  git clone --depth 1 -b "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
elif [ -d "$INSTALL_DIR/.git" ]; then
  if [ "$ALLOW_UPDATE" = "1" ]; then
    info "Updating existing repo in $INSTALL_DIR"
    git -C "$INSTALL_DIR" pull --ff-only
  else
    printf 'Install dir exists. Set ALLOW_UPDATE=1 to update: %s\n' "$INSTALL_DIR" >&2
    exit 1
  fi
else
  printf 'Install dir exists but is not a git repo: %s\n' "$INSTALL_DIR" >&2
  exit 1
fi

cd "$INSTALL_DIR"

if [ ! -f config.yaml ]; then
  info 'Creating config.yaml from example'
  cp config.example.yaml config.yaml
fi

if [ ! -f web_config.json ]; then
  info 'Creating web_config.json from example'
  cp web_config.example.json web_config.json
fi

if [ ! -f report_state.json ]; then
  info 'Creating report_state.json from example'
  cp report_state.example.json report_state.json
fi

AUTOMATION_DIR="${INSTALL_DIR}/automation"
if [[ ! -d "${AUTOMATION_DIR}" ]]; then
  echo "Missing automation directory in ${INSTALL_DIR}. Please check the repo contents." >&2
  exit 1
fi

write_map_yaml() {
  local input="$1"
  local indent="$2"
  IFS=',' read -ra PAIRS <<< "${input}"
  for pair in "${PAIRS[@]}"; do
    if [[ -z "${pair}" ]]; then
      continue
    fi
    local key="${pair%%=*}"
    local val="${pair#*=}"
    printf "%s\"%s\": \"%s\"\n" "${indent}" "${key}" "${val}"
  done
}

if [[ -n "${HETZNER_API_TOKEN:-}" ]]; then
  if [[ ! -f "${AUTOMATION_DIR}/config.yaml" || "${FORCE_CONFIG}" = "1" ]]; then
    info "Writing automation/config.yaml from environment variables"
    cat > "${AUTOMATION_DIR}/config.yaml" <<EOF
hetzner:
  api_token: "${HETZNER_API_TOKEN}"

traffic:
  limit_gb: ${LIMIT_GB:-18000}
  check_interval: ${CHECK_INTERVAL:-5}
  exceed_action: "${EXCEED_ACTION:-delete_rebuild}"
  confirm_before_delete: false
  warning_thresholds:
    - 10
    - 20
    - 30
    - 40
    - 50
    - 60
    - 70
    - 80
    - 90
    - 95
    - 100

scheduler:
  enabled: false
  tasks: []

telegram:
  enabled: true
  bot_token: "${TELEGRAM_BOT_TOKEN:-}"
  chat_id: "${TELEGRAM_CHAT_ID:-}"
  notify_on:
    - traffic_warning
    - traffic_exceeded
    - server_deleted

cloudflare:
  api_token: "${CF_API_TOKEN:-}"
  zone_id: "${CF_ZONE_ID:-}"
  record_map:
EOF
    if [[ -n "${CF_RECORD_MAP:-}" ]]; then
      write_map_yaml "${CF_RECORD_MAP}" "    " >> "${AUTOMATION_DIR}/config.yaml"
    else
      echo "    \"SERVER_ID\": \"host.example.com\"" >> "${AUTOMATION_DIR}/config.yaml"
    fi

    cat >> "${AUTOMATION_DIR}/config.yaml" <<EOF

notifications:
  email:
    enabled: false
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    username: ""
    password: ""
    to_addresses: []

logging:
  level: "INFO"
  file: "hetzner_monitor.log"
  max_size_mb: 10
  backup_count: 5

whitelist:
  server_ids: []
  server_names: []

server_template:
  server_type: "${SERVER_TYPE:-cx43}"
  location: "${LOCATION:-nbg1}"
  ssh_keys: []
  name_prefix: "auto-"
  use_original_name: true

snapshot_map:
EOF
    if [[ -n "${SNAPSHOT_MAP:-}" ]]; then
      write_map_yaml "${SNAPSHOT_MAP}" "  " >> "${AUTOMATION_DIR}/config.yaml"
    else
      echo "  SERVER_ID: SNAPSHOT_ID" >> "${AUTOMATION_DIR}/config.yaml"
    fi
  else
    info "automation/config.yaml exists; skipping auto-config"
  fi
else
  info "No HETZNER_API_TOKEN provided; automation will use config.example.yaml"
fi

info 'Build and start web containers'
$COMPOSE up -d --build

info 'Install and start automation service'
chmod +x "${AUTOMATION_DIR}/install.sh"
cd "${AUTOMATION_DIR}"
./install.sh

info 'Done. Edit config.yaml, web_config.json, and automation/config.yaml if needed.'
