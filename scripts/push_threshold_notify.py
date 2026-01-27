#!/usr/bin/env python3
import argparse
import os
import sys
from decimal import Decimal, ROUND_HALF_UP

import requests
import yaml


def _bytes_to_tb(value_bytes: float) -> Decimal:
    return (Decimal(value_bytes) / (Decimal(1024) ** 4)).quantize(
        Decimal("0.001"), rounding=ROUND_HALF_UP
    )


def _bytes_to_tb_precise(value_bytes: float, places: str = "0.000") -> Decimal:
    return (Decimal(value_bytes) / (Decimal(1024) ** 4)).quantize(
        Decimal(places), rounding=ROUND_HALF_UP
    )


def _progress_bar(percent: float) -> str:
    bars = int(max(0, min(100, percent)) / 10)
    return "█" * bars + "░" * (10 - bars)


def main() -> int:
    parser = argparse.ArgumentParser(description="Send threshold notifications once.")
    parser.add_argument(
        "--config",
        default=os.environ.get("HETZNER_CONFIG_PATH", "config.yaml"),
        help="配置文件路径 (默认: $HETZNER_CONFIG_PATH 或 config.yaml)",
    )
    args = parser.parse_args()

    config = yaml.safe_load(open(args.config, "r", encoding="utf-8"))
    telegram = config.get("telegram") or {}
    bot_token = telegram.get("bot_token") or ""
    chat_id = str(telegram.get("chat_id") or "").strip()
    if not bot_token or not chat_id:
        print("telegram bot_token/chat_id 未配置")
        return 1

    traffic = config.get("traffic") or {}
    limit_gb = traffic.get("limit_gb")
    if not limit_gb:
        print("traffic.limit_gb 未配置")
        return 1
    limit_bytes = float(Decimal(limit_gb) * (Decimal(1024) ** 3))
    limit_tb = (Decimal(limit_bytes) / (Decimal(1024) ** 4)).quantize(Decimal("0.001"))

    hetzner = config.get("hetzner") or {}
    api_token = hetzner.get("api_token") or ""
    if not api_token:
        print("hetzner.api_token 未配置")
        return 1
    headers = {"Authorization": f"Bearer {api_token}"}
    servers = requests.get(
        "https://api.hetzner.cloud/v1/servers", headers=headers, timeout=20
    ).json()["servers"]

    emojis = {
        10: "💧",
        20: "💦",
        30: "🌊",
        40: "🟢",
        50: "🟡",
        60: "🟠",
        70: "🔶",
        80: "🔴",
        90: "🚨",
        100: "💀",
    }
    levels = telegram.get("notify_levels") or []

    sent = 0
    for s in servers:
        detail = requests.get(
            f"https://api.hetzner.cloud/v1/servers/{s['id']}",
            headers=headers,
            timeout=20,
        ).json()["server"]
        outgoing = detail.get("outgoing_traffic")
        if outgoing is None:
            continue
        percent = (float(outgoing) / limit_bytes) * 100
        reached = [level for level in levels if percent >= level]
        if not reached:
            continue
        threshold = max(reached)
        emoji = emojis.get(threshold, "📊")
        outbound_tb = _bytes_to_tb(float(outgoing))
        inbound_tb = _bytes_to_tb_precise(float(detail.get("ingoing_traffic") or 0))
        outbound_tb_precise = _bytes_to_tb_precise(float(outgoing))
        remaining_tb = (limit_tb - outbound_tb).quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        )
        bar = _progress_bar(percent)
        server_name = detail.get("name") or s.get("name") or s["id"]
        msg = (
            f"{emoji} *流量通知 - {threshold}%*\n\n"
            f"🖥 服务器: *{server_name}*\n"
            f"📊 使用进度:\n"
            f"`{bar}` {percent:.1f}%\n\n"
            f"💾 已用(出站): *{outbound_tb} TB* / {limit_tb} TB\n"
            f"📉 剩余: {remaining_tb} TB\n\n"
            f"📤 出站: {outbound_tb_precise} TB\n"
            f"📥 入站: {inbound_tb} TB"
        )
        resp = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"},
            timeout=20,
        )
        print(server_name, resp.status_code)
        if resp.ok:
            sent += 1

    print("sent", sent)
    return 0


if __name__ == "__main__":
    sys.exit(main())
