# Hetzner Web

[English](README.md) | [中文](README.zh.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED)](#快速开始-docker)

一个轻量的 Hetzner 流量控制台，提供日/小时视图、重建操作、DNS 检查和清晰的仪表盘。

## 关于

Hetzner Web 是面向 Hetzner Cloud 的流量可视化控制室。它把原始流量数据整理成日/小时洞察，
突出流量触顶风险，并把重建/DNS 操作放在图表旁边，方便快速处理。

## 导航

- Web 控制台快速安装（只装 Web 控制台）：
  `curl -fsSL https://raw.githubusercontent.com/liuweiqiang0523/Hetzner-Web/main/scripts/install-docker.sh | bash`
- 自动化监控快速安装（只装 automation 服务）：
  `curl -fsSL https://raw.githubusercontent.com/liuweiqiang0523/Hetzner-Web/main/automation/install_hetzner_monitor.sh | sudo bash`
- 自动化文档：`automation/README_CN.md`

## 我该装哪一个？

- 只想要网页仪表盘、手动重建、可视化统计：只装 **Web 控制台**（Docker）。
- 只想要自动化告警/自动重建（后台服务）：只装 **automation**（CLI/Systemd）。
- 既要网页又要自动化：**两个都装**（互不冲突）。

## 截图

![Dashboard](docs/screenshot.png)

## 功能

- 实时服务器流量（出站/入站）
- 日/小时拆分表 + 每日单机柱状图
- DNS 检查/同步 + 重建操作
- Telegram 机器人查询与管理
- 快照重建 + 按快照创建
- 定时删机/建机
- 每台机器的趋势火花线
- Basic Auth 登录

## 项目结构

- Web 控制台（本目录）：FastAPI + Vue，Docker 优先。
- 自动化监控：`automation/`（CLI/systemd 服务）。

快捷入口：
- Web 文档：`README.zh.md`（当前）
- 自动化文档：`automation/README_CN.md`
- 自动化安装脚本：`automation/install_hetzner_monitor.sh`

## 工作方式

- 刷新时从 Hetzner Cloud API 拉取服务器与流量数据。
- 将原始数值汇总成日/小时序列，并缓存到 `report_state.json`。
- 前端为静态 Vue 面板，通过 `/api/*` 接口渲染图表。

## 技术栈

- 后端：FastAPI + Python
- 前端：Vue 3（CDN）+ 原生 JS/CSS

## 安装前需要准备

- 一台可联网的 Linux 服务器（有公网 IP）
- Docker 与 Docker Compose
- Hetzner Cloud API Token（必填，写入 `config.yaml`）
- Web 登录账号密码（必填，写入 `web_config.json`）
- 可选：Telegram Bot Token + Chat ID（需要通知/机器人）
- 可选：Cloudflare API Token + Zone ID（需要 DNS 同步/检查）

## 快速开始 (Docker)

用途：手动安装（本地已有代码时使用）。

```bash
cp config.example.yaml config.yaml
cp web_config.example.json web_config.json
cp report_state.example.json report_state.json
# 编辑 config.yaml + web_config.json

docker compose up -d --build
```

打开：`http://<server-ip>:1227`

## 一键安装 (Docker)

用途：全新安装（自动下载仓库并启动）。
二选一即可，**不要重复安装**。

```bash
curl -fsSL https://raw.githubusercontent.com/liuweiqiang0523/Hetzner-Web/main/scripts/install-docker.sh | bash
```

可选环境变量：
- `INSTALL_DIR`：安装目录（默认 `/opt/hetzner-web`）
- `BRANCH`：分支（默认 `main`）
- `REPO_URL`：仓库地址

示例：

```bash
curl -fsSL https://raw.githubusercontent.com/liuweiqiang0523/Hetzner-Web/main/scripts/install-docker.sh | INSTALL_DIR=/srv/hetzner-web bash
```

## 自动化监控 (CLI/Systemd)

原 Hetzner 自动化监控项目已合并到本仓库的 `automation/` 目录。

- 入口：`automation/main.py`
- 安装文档：`automation/INSTALL.md`（English）、`automation/INSTALL_CN.md`（中文）
- 一键安装脚本：`automation/install_hetzner_monitor.sh`

这样可以在同一个仓库中维护 Web 控制台与自动化服务，互不影响。

## 反向代理 (Nginx 示例)

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

## 配置

### `config.yaml`
- `hetzner.api_token`: Hetzner Cloud API token
- `traffic.limit_gb`: 流量上限 (GB)
- `traffic.check_interval`: 轮询频率（分钟）
- `traffic.exceed_action`: 超限动作（`rebuild` 或留空）
- `scheduler.enabled`: 是否开启定时任务
- `scheduler.delete_time`: 删除时间（HH:MM，逗号分隔）
- `scheduler.create_time`: 创建时间（HH:MM，逗号分隔）
- `telegram.bot_token`: Telegram Bot Token
- `telegram.chat_id`: Telegram Chat ID
- `telegram.notify_levels`: 告警阈值（百分比）
- `telegram.daily_report_time`: 每日战报时间（HH:MM）
- `cloudflare.api_token`: Cloudflare API Token
- `cloudflare.zone_id`: Cloudflare Zone ID
- `cloudflare.sync_on_start`: 启动时同步 DNS
- `cloudflare.record_map`: server_id 或 server_name -> DNS 记录
- `rebuild.snapshot_id_map`: server_id -> snapshot_id
- `rebuild.fallback_template`: 重建时回退模板

### `web_config.json`
- `username` / `password`: Basic Auth 凭据
- `tracking_start`: 可选，如 `2026-01-01 00:00`

## Telegram 命令

查询类：
- `/list`：服务器列表
- `/status`：系统状态
- `/traffic ID`：流量详情（不带 ID 显示全部）
- `/today ID`：今日流量（不带 ID 显示全部）
- `/report`：手动流量汇报
- `/reportstatus`：上次汇报时间
- `/reportreset`：重置汇报区间
- `/dnstest ID`：测试 DNS 更新
- `/dnscheck ID`：DNS 解析检查

控制类：
- `/startserver <ID>`：启动服务器
- `/stopserver <ID>`：停止服务器
- `/reboot <ID>`：重启服务器
- `/delete <ID> confirm`：删除服务器
- `/rebuild <ID>`：重建服务器

快照管理：
- `/snapshots`：查看快照
- `/createsnapshot <ID>`：创建快照
- `/createfromsnapshot <SNAP_ID>`：按快照创建服务器
- `/createfromsnapshots`：按映射快照批量创建

定时任务：
- `/scheduleon`：开启定时删机
- `/scheduleoff`：关闭定时删机
- `/schedulestatus`：查看定时状态
- `/scheduleset delete=23:50,01:00 create=08:00,09:00`：设置定时

DNS：
- `/dnsync`：同步 Cloudflare DNS

> `cloudflare.record_map` 支持对象格式：`{ record, zone_id, api_token }`，可为不同服务器配置不同 Zone。

## 安全说明

- `config.yaml` 和 `web_config.json` 为敏感文件（已加入 gitignore）。
- 建议通过 HTTPS 反向代理访问。
- 可结合 IP 白名单限制访问。

## 备注

- 运行时数据存放在 `report_state.json`（已加入 gitignore）。
- `config.yaml` 和 `web_config.json` 已加入 gitignore，避免泄露。

## 版本发布

仓库统一版本说明见 `RELEASE_NOTES.md`，适用于 Web 控制台与自动化监控。

## 许可证

MIT
