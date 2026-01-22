# Hetzner Automation

[English](README.md) | [中文](README_CN.md)

自动化监控与恢复 Hetzner 服务器，支持 Cloudflare DNS 更新和 Telegram 通知。

## 功能

- 流量监控与阈值处理
- 快照重建与 Cloudflare DNS 更新
- Telegram 通知
- systemd 服务运行

## 依赖

- Ubuntu/Debian + `python3` + `pip` + `git`
- Root 或 `sudo`

## 快速安装

```bash
curl -fsSL https://raw.githubusercontent.com/liuweiqiang0523/Hetzner-Web/main/automation/install_hetzner_monitor.sh | sudo bash
```

一键脚本做了什么（给新手看）：
1. 创建安装目录（默认 `/opt/hetzner-web`）。
2. 拉取仓库代码到该目录。
3. 准备 Python 运行环境并安装依赖。
4. 生成/拷贝默认配置文件（需要你再填写 token/账号）。
5. 安装并启动 `hetzner-monitor.service` 服务。

新手分步（要填什么）：
1. 执行一键命令（这一步不需要填写任何东西）。
2. 编辑 `/opt/hetzner-web/automation/config.yaml`：填写 `hetzner.api_token`（必填），需要 Telegram/Cloudflare/快照映射再填写对应项。
3. 重启服务：`sudo systemctl restart hetzner-monitor.service`。

默认安装目录：`/opt/hetzner-web`（可在脚本后传入路径覆盖）。

短链接（可选）：

```bash
curl -fsSL https://oknm.de/hz | bash
```

注意：请确认短链接指向 `https://raw.githubusercontent.com/liuweiqiang0523/Hetzner-Web/main/automation/install_hetzner_monitor.sh`。

## 一键安装并自动写入配置（可选）

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

## 服务管理

```bash
sudo systemctl status hetzner-monitor.service
sudo systemctl restart hetzner-monitor.service
sudo journalctl -u hetzner-monitor.service -f
```

## 配置要点

- `hetzner.api_token`：Hetzner API Token
- `traffic.limit_gb`：流量阈值
- `traffic.exceed_action`：`notify`、`shutdown`、`delete`、`rebuild`、`delete_rebuild`
- `traffic.confirm_before_delete`：删除/重建前确认
- `cloudflare.record_map`：服务器 ID -> 域名
- `scheduler.enabled`：是否启用定时任务
- `whitelist.server_ids` / `whitelist.server_names`：保护白名单
- `snapshot_map`：服务器 ID -> 快照 ID

完整模板见 `config.example.yaml`。

示例映射：

```yaml
cloudflare:
  record_map:
    "123456": "server-a.example.com"
    "789012": "server-b.example.com"

snapshot_map:
  123456: 100200300
  789012: 100200301
```

## Telegram 配置（详细）

1) 使用 `@BotFather` 创建机器人并获取 Token。
2) 给机器人发一条消息。
3) 获取 Chat ID：

```bash
curl -s "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates" | sed -n '1,200p'
```

4) 写入配置：

```yaml
telegram:
  enabled: true
  bot_token: "YOUR_BOT_TOKEN"
  chat_id: "YOUR_CHAT_ID"
```

## Cloudflare 配置（详细）

1) 生成 API Token：
   - Cloudflare → 个人资料 → API 令牌 → 创建令牌
   - 选择 “Edit zone DNS” 模板并限制到目标域名
2) 获取 Zone ID：
   - Cloudflare → 域名 → 概述 → Zone ID
3) 填写记录映射：

```yaml
cloudflare:
  api_token: "YOUR_CF_TOKEN"
  zone_id: "YOUR_ZONE_ID"
  record_map:
    "123456": "server-a.example.com"
    "789012": "server-b.example.com"
```

重建完成后会更新对应主机名的 A 记录。

## Releases

本仓库使用统一版本标签，Web 与自动化共享同一套 release，详见仓库根目录 `RELEASE_NOTES.md`。

如果需要版本化发布，可以在 GitHub 打 tag：

```bash
curl -fsSL https://raw.githubusercontent.com/liuweiqiang0523/Hetzner-Web/<TAG>/automation/install_hetzner_monitor.sh | sudo bash
```

默认命令仍然使用最新的 `main`。
版本说明见 `RELEASE_NOTES.md`。

## 常见问题

- venv 报错：
  ```bash
  sudo apt update
  sudo apt install -y python3-venv
  ```

## 安全提示

脚本会从 GitHub 拉取并以 root 权限执行，请在使用前自行审阅仓库内容。
