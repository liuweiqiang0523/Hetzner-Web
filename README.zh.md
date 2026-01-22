![Hetzner-Web](docs/brand-logo.svg)

[English](README.md) | [中文](README.zh.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED)](#快速开始)

一个轻量的 Hetzner 流量控制台 + 自动化监控工具。支持可视化仪表盘、Telegram 通知/命令、自动重建、DNS 检查。

---

<table>
  <tr>
    <td width="60%" valign="top">
      <strong>从这里开始</strong><br />
      一条命令装好 Web + automation + Telegram。<br /><br />
      <code>curl -fsSL https://raw.githubusercontent.com/liuweiqiang0523/Hetzner-Web/main/scripts/install-all.sh | sudo bash</code>
    </td>
    <td width="40%" valign="top">
      <strong>下一步</strong><br />
      填写配置并重启服务。<br /><br />
      <code>config.yaml</code> · <code>web_config.json</code> · <code>automation/config.yaml</code>
    </td>
  </tr>
</table>

---

## 目录

- [快速开始](#快速开始)
- [界面截图](#界面截图)
- [亮点功能](#亮点功能)
- [安装方式](#安装方式)
- [环境要求](#环境要求)
- [配置设置](#配置设置)
- [Telegram 配置](#telegram-配置)
- [配置文件位置](#配置文件位置)
- [排错指南](#排错指南)
- [项目结构](#项目结构)
- [功能一览](#功能一览)
- [安全说明](#安全说明)
- [品牌色卡](#品牌色卡)

---

## ![Start](docs/icon-start.svg) 快速开始

第一次使用直接选二合一脚本，一次性装好 Web + automation + Telegram 支持。

```bash
curl -fsSL https://raw.githubusercontent.com/liuweiqiang0523/Hetzner-Web/main/scripts/install-all.sh | sudo bash
```

然后继续看「配置设置」。

![安装流程](docs/quickstart-flow.light.svg)

---

## ![Camera](docs/icon-camera.svg) 界面截图

![Web 控制台](docs/web.png)
![Telegram 机器人](docs/telegram.png)

---

## ![List](docs/icon-list.svg) 亮点功能

![Feature Cards](docs/feature-cards.svg)

---

## ![Install](docs/icon-install.svg) 安装方式

- 二合一（推荐）：`scripts/install-all.sh`
- 只装 Web：`scripts/install-docker.sh`
- 只装 automation：`automation/install_hetzner_monitor.sh`

默认不会影响已有部署。二合一脚本发现目录已存在会直接退出。如果你确实要更新已有安装：

```bash
curl -fsSL https://raw.githubusercontent.com/liuweiqiang0523/Hetzner-Web/main/scripts/install-all.sh | sudo ALLOW_UPDATE=1 bash
```

---

## ![Check](docs/icon-check.svg) 环境要求

先确认这些命令可用：

```bash
git --version
python3 --version
docker --version
docker compose version
systemctl --version
```

如果缺少，请先安装（Ubuntu/Debian 可用 apt）。

---

## ![Config](docs/icon-config.svg) 配置设置

**Web 配置**
- `config.yaml`：填写 `hetzner.api_token`
- `web_config.json`：填写 `username` / `password`

**Automation 配置**
- `automation/config.yaml`：填写 Hetzner/Telegram/Cloudflare 等

应用配置：

```bash
cd /opt/hetzner-web

docker compose up -d --build
sudo systemctl restart hetzner-monitor.service
```

打开：`http://<你的服务器IP>:1227`

---

## ![Telegram](docs/icon-telegram.svg) Telegram 配置

在 `automation/config.yaml` 中填：

```yaml
telegram:
  enabled: true
  bot_token: "你的 Bot Token"
  chat_id: "你的 Chat ID"
```

然后重启 automation：

```bash
sudo systemctl restart hetzner-monitor.service
```

---

## ![Map](docs/icon-map.svg) 配置文件位置

![配置文件速查](docs/config-files.light.svg)

- Web：`/opt/hetzner-web/config.yaml`
- Web 登录：`/opt/hetzner-web/web_config.json`
- Automation：`/opt/hetzner-web/automation/config.yaml`

---

## ![Tools](docs/icon-tools.svg) 排错指南

![排错流程](docs/troubleshooting-flow.light.svg)

一键自检：
- `docker ps`
- `sudo systemctl status hetzner-monitor.service`
- `sudo journalctl -u hetzner-monitor.service -n 50 --no-pager`

---

## ![Layout](docs/icon-layout.svg) 项目结构

- Web 控制台（本目录）：FastAPI + Vue，Docker 优先
- 自动化监控：`automation/`（CLI/Systemd 服务）

相关文档：
- Automation 说明：`automation/README_CN.md`

---

## ![List](docs/icon-list.svg) 功能一览

- 实时服务器流量（出站/入站）
- 日/小时拆分表 + 每日单机柱状图
- DNS 检查/同步 + 重建操作
- Telegram 机器人查询与管理
- 快照重建 + 按快照创建
- 定时删机/建机
- 每台机器的趋势火花线
- Basic Auth 登录

---

## ![Shield](docs/icon-shield.svg) 安全说明

- `config.yaml` / `web_config.json` / `automation/config.yaml` 都是敏感文件，请不要提交到 Git。
- 建议通过 HTTPS 反向代理访问。

---

## 品牌色卡

![Brand Palette](docs/brand-palette.svg)
