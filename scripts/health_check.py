#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request

DEFAULT_CONFIG = "/opt/hetzner-web/config.yaml"
DEFAULT_REPORT = "/opt/hetzner-web/report_state.json"
DEFAULT_THRESHOLD = "/opt/hetzner-web/threshold_state.json"
DEFAULT_STATE = "/opt/hetzner-web/health_state.json"
DEFAULT_CONTAINER = "hetzner-web"


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if (value.startswith("\"") and value.endswith("\"")) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value


def _parse_telegram_config(path: str):
    enabled = None
    bot_token = None
    chat_id = None
    if not os.path.exists(path):
        return enabled, bot_token, chat_id

    in_telegram = False
    base_indent = None
    key_re = re.compile(r"^([A-Za-z0-9_]+)\s*:\s*(.*)$")

    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            indent = len(line) - len(line.lstrip(" "))
            if line.strip() == "telegram:":
                in_telegram = True
                base_indent = indent
                continue
            if in_telegram:
                if indent <= (base_indent or 0):
                    break
                m = key_re.match(line.strip())
                if not m:
                    continue
                key, value = m.group(1), m.group(2)
                value = value.split("#", 1)[0].strip()
                value = _strip_quotes(value)
                if key == "enabled":
                    enabled = value.lower() in ("true", "1", "yes", "y")
                elif key == "bot_token":
                    bot_token = value
                elif key == "chat_id":
                    chat_id = value

    return enabled, bot_token, chat_id


def _send_telegram(bot_token: str, chat_id: str, text: str) -> bool:
    if not bot_token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return 200 <= resp.status < 300
    except Exception:
        return False


def _check_container(name: str):
    try:
        proc = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", name],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception as exc:
        return False, f"docker inspect failed: {exc}"
    if proc.returncode != 0:
        return False, (proc.stderr.strip() or proc.stdout.strip() or "container not found")
    return proc.stdout.strip() == "true", proc.stdout.strip()


def _check_file_fresh(path: str, max_age_seconds: int):
    if not os.path.exists(path):
        return False, "missing"
    mtime = os.path.getmtime(path)
    age = int(time.time() - mtime)
    ok = age <= max_age_seconds
    return ok, f"age={age}s"


def _load_state(path: str):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_state(path: str, data: dict):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Hetzner-Web health check")
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--report", default=DEFAULT_REPORT)
    parser.add_argument("--threshold", default=DEFAULT_THRESHOLD)
    parser.add_argument("--container", default=DEFAULT_CONTAINER)
    parser.add_argument("--state-file", default=DEFAULT_STATE)
    parser.add_argument("--max-age-min", type=int, default=10)
    parser.add_argument("--notify-ok", action="store_true")
    parser.add_argument("--notify-ok-daily", action="store_true")
    args = parser.parse_args()

    enabled, bot_token, chat_id = _parse_telegram_config(args.config)
    if enabled is False:
        return 0

    failures = []
    checks = []

    ok, info = _check_container(args.container)
    checks.append(("container", ok, info))
    if not ok:
        failures.append("container")

    max_age_seconds = max(60, args.max_age_min * 60)
    ok, info = _check_file_fresh(args.report, max_age_seconds)
    checks.append(("report_state", ok, info))
    if not ok:
        failures.append("report_state")

    ok, info = _check_file_fresh(args.threshold, max_age_seconds * 6)
    checks.append(("threshold_state", ok, info))
    # threshold_state is soft-check: do not fail

    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if failures:
        lines = [f"[Health] ❌ Unhealthy @ {now}"]
        for name, ok, info in checks:
            status = "OK" if ok else "FAIL"
            lines.append(f"- {name}: {status} ({info})")
        _send_telegram(bot_token or "", chat_id or "", "\n".join(lines))
        return 1

    if args.notify_ok or args.notify_ok_daily:
        state = _load_state(args.state_file)
        today = dt.date.today().isoformat()
        last_ok = state.get("last_ok_date")
        if args.notify_ok or last_ok != today:
            lines = [f"[Health] ✅ OK @ {now}"]
            for name, ok, info in checks:
                status = "OK" if ok else "FAIL"
                lines.append(f"- {name}: {status} ({info})")
            if _send_telegram(bot_token or "", chat_id or "", "\n".join(lines)):
                state["last_ok_date"] = today
                _save_state(args.state_file, state)

    return 0


if __name__ == "__main__":
    sys.exit(main())
