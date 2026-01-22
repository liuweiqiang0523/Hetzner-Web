# 安装（单命令脚本）

[English](INSTALL.md) | [中文](INSTALL_CN.md)

## 前置条件
- Ubuntu/Debian，已安装 `python3`、`pip`、`git`
- Root 权限（或 `sudo`）

## 步骤
1) 把仓库复制到目标机器。
2) 执行：

```bash
sudo ./install.sh
```

### 一行安装（可选）
```bash
curl -fsSL https://raw.githubusercontent.com/liuweiqiang0523/Hetzner-Web/main/automation/install_hetzner_monitor.sh | sudo bash
```

一键脚本做了什么（给新手看）：
1. 创建安装目录（默认 `/opt/hetzner-web`）。
2. 拉取仓库代码到该目录。
3. 准备 Python 运行环境并安装依赖。
4. 生成/拷贝默认配置文件（需要你再填写 token/账号）。
5. 安装并启动 `hetzner-monitor.service` 服务。

默认安装目录：`/opt/hetzner-web`（可在脚本后传入路径覆盖）。

### 短链接安装（可选）
```bash
curl -fsSL https://oknm.de/hz | bash
```

注意：请确认短链接指向 `https://raw.githubusercontent.com/liuweiqiang0523/Hetzner-Web/main/automation/install_hetzner_monitor.sh`。

### 一行安装并自动配置（可选）
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

3) 编辑配置：

```bash
sudo nano /opt/hetzner-web/automation/config.yaml
```

填写：
- Hetzner API Token
- Telegram Bot Token + Chat ID
- Cloudflare API Token + Zone ID + record map
- Snapshot map（server ID -> snapshot ID）

4) 重启服务：

```bash
sudo systemctl restart hetzner-monitor.service
```

## 服务
```bash
sudo systemctl status hetzner-monitor.service
sudo journalctl -u hetzner-monitor.service -f
```

## 常见问题

- venv 报错（Debian/Ubuntu）：
  ```bash
  sudo apt update
  sudo apt install -y python3-venv
  ```

## 安全提示

脚本会从 GitHub 拉取并以 root 权限执行，请在使用前自行审阅仓库内容。
