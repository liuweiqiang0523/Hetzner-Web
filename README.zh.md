# Hetzner Web

[English](README.md) | [中文](README.zh.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED)](#30-秒上手二合一推荐)

一个轻量的 Hetzner 流量控制台 + 自动化监控工具。支持可视化仪表盘、Telegram 通知/命令、自动重建、DNS 检查。

---

## 30 秒上手（二合一推荐）

如果你是第一次用，**直接用二合一脚本**，一次性装好 Web + automation + Telegram 支持。

```bash
curl -fsSL https://raw.githubusercontent.com/liuweiqiang0523/Hetzner-Web/main/scripts/install-all.sh | sudo bash
```

安装完成后，继续看下面「**配置填写**」。

![安装流程](docs/quickstart-flow.svg)

---

## 我该装哪一个？

- 新手/省事：用 **二合一脚本**（Web + automation + Telegram）。
- 只要网页仪表盘：用 **Web 一键脚本**。
- 只要自动化监控：用 **automation 一键脚本**。

---

## 先确认环境（新手必看）

脚本不会帮你装系统依赖，请先确认这些命令可用：

```bash
git --version
python3 --version
docker --version
docker compose version
systemctl --version
```

如果缺少，请先安装对应组件（Ubuntu/Debian 通常可用 apt 安装）。

---

## 二合一一键安装（推荐）

### 1) 运行脚本

```bash
curl -fsSL https://raw.githubusercontent.com/liuweiqiang0523/Hetzner-Web/main/scripts/install-all.sh | sudo bash
```

### 2) 填写配置（非常重要）

**Web 配置：**
- `config.yaml`：填写 `hetzner.api_token`。
- `web_config.json`：填写 `username` / `password`。

**Automation 配置：**
- `automation/config.yaml`：填写 Hetzner/Telegram/Cloudflare 等（如需通知）。

> 注意：如果脚本没有检测到 `HETZNER_API_TOKEN`，会先使用示例配置。你一定要手动填写。

### 3) 重启让配置生效

```bash
cd /opt/hetzner-web

docker compose up -d --build
sudo systemctl restart hetzner-monitor.service
```

### 4) 打开网页

浏览器访问：`http://<你的服务器IP>:1227`

---

## Telegram 配置（最常用）

在 `automation/config.yaml` 中填：

```yaml
telegram:
  enabled: true
  bot_token: "你的 Bot Token"
  chat_id: "你的 Chat ID"
```

填完重启 automation：

```bash
sudo systemctl restart hetzner-monitor.service
```

---

## 只装 Web（可选）

```bash
curl -fsSL https://raw.githubusercontent.com/liuweiqiang0523/Hetzner-Web/main/scripts/install-docker.sh | bash
```

装完后填写：`config.yaml` + `web_config.json`，然后执行：

```bash
docker compose up -d --build
```

---

## 只装 Automation（可选）

```bash
curl -fsSL https://raw.githubusercontent.com/liuweiqiang0523/Hetzner-Web/main/automation/install_hetzner_monitor.sh | sudo bash
```

装完后填写：`automation/config.yaml`，然后执行：

```bash
sudo systemctl restart hetzner-monitor.service
```

---

## 已有部署会被改动吗？

默认 **不会**。

二合一脚本遇到已存在的目录会直接退出，避免覆盖你现有的部署。

如果你明确要更新已有目录（不推荐新手）：

```bash
curl -fsSL https://raw.githubusercontent.com/liuweiqiang0523/Hetzner-Web/main/scripts/install-all.sh | sudo ALLOW_UPDATE=1 bash
```

---

## 配置文件在哪里？

![配置文件速查](docs/config-files.svg)

- Web：`/opt/hetzner-web/config.yaml`
- Web 登录：`/opt/hetzner-web/web_config.json`
- Automation：`/opt/hetzner-web/automation/config.yaml`

---

## 排错图（新手必备）

![排错流程](docs/troubleshooting-flow.svg)

一键自检：
- `docker ps`
- `sudo systemctl status hetzner-monitor.service`
- `sudo journalctl -u hetzner-monitor.service -n 50 --no-pager`

---

## 项目结构

- Web 控制台（本目录）：FastAPI + Vue，Docker 优先。
- 自动化监控：`automation/`（CLI/Systemd 服务）。

相关文档：
- Web 说明：`README.zh.md`（当前文件）
- Automation 说明：`automation/README_CN.md`

---

## 功能一览

- 实时服务器流量（出站/入站）
- 日/小时拆分表 + 每日单机柱状图
- DNS 检查/同步 + 重建操作
- Telegram 机器人查询与管理
- 快照重建 + 按快照创建
- 定时删机/建机
- 每台机器的趋势火花线
- Basic Auth 登录

---

## 安全说明

- `config.yaml` / `web_config.json` / `automation/config.yaml` 都是敏感文件，请不要提交到 Git。
- 建议通过 HTTPS 反向代理访问。

---

## Telegram 常用命令（附录）

查询类：
- `/list`：服务器列表
- `/status`：系统状态
- `/traffic ID`：流量详情
- `/today ID`：今日流量
- `/report`：手动流量汇报
- `/dnstest ID`：测试 DNS 更新
- `/dnscheck ID`：DNS 解析检查

控制类：
- `/startserver <ID>`：启动服务器
- `/stopserver <ID>`：停止服务器
- `/reboot <ID>`：重启服务器
- `/delete <ID> confirm`：删除服务器
- `/rebuild <ID>`：重建服务器

