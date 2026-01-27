#!/usr/bin/env python3
import yaml
import logging
import time
import argparse
import threading
import asyncio
from logging.handlers import RotatingFileHandler

from hetzner_manager import HetznerManager
from traffic_monitor import TrafficMonitor
from scheduler import TaskScheduler
from notifier import Notifier

# 尝试导入 Telegram Bot
try:
    from telegram_bot import TelegramBot
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    TelegramBot = None


def setup_logging(config: dict) -> logging.Logger:
    log_config = config['logging']
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_config['level']))
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    file_handler = RotatingFileHandler(
        log_config['file'],
        maxBytes=log_config['max_size_mb'] * 1024 * 1024,
        backupCount=log_config['backup_count']
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    return logger


def load_config(config_path: str = 'config.yaml') -> dict:
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"❌ 配置文件不存在: {config_path}")
        exit(1)
    except Exception as e:
        print(f"❌ 加载配置文件失败: {e}")
        exit(1)


def check_config(config: dict) -> bool:
    api_token = config['hetzner']['api_token']
    if not api_token or api_token == 'YOUR_HETZNER_API_TOKEN':
        print("❌ 请在 config.yaml 中设置您的 Hetzner API Token")
        return False
    return True


def run_telegram_bot(bot):
    """在单独线程中运行 Telegram Bot"""
    try:
        if bot.initialize_commands():
            bot.run_polling()
    except Exception as e:
        logging.error(f"Telegram Bot 运行错误: {e}")


def main():
    parser = argparse.ArgumentParser(description='Hetzner 服务器流量监控系统')
    parser.add_argument('--config', default='config.yaml', help='配置文件路径')
    parser.add_argument('--once', action='store_true', help='只运行一次检查')
    parser.add_argument('--dry-run', action='store_true', help='只演练流程，不执行删除/重建')
    parser.add_argument('--list', action='store_true', help='列出所有服务器')
    parser.add_argument('--check-traffic', type=int, metavar='SERVER_ID', help='检查指定服务器流量')
    
    args = parser.parse_args()
    config = load_config(args.config)
    config['_config_path'] = args.config
    
    if not check_config(config):
        return
    
    logger = setup_logging(config)
    logger.info("=" * 70)
    logger.info("Hetzner 服务器监控系统启动")
    logger.info("=" * 70)
    
    hetzner = HetznerManager(config['hetzner']['api_token'])
    monitor = TrafficMonitor(hetzner, config)
    scheduler = TaskScheduler(hetzner, config)
    notifier = Notifier(config)
    
    # 初始化 Telegram Bot
    telegram_bot = None
    if TELEGRAM_AVAILABLE and config.get('telegram', {}).get('enabled'):
        logger.info("正在初始化 Telegram Bot...")
        telegram_bot = TelegramBot(config, hetzner, monitor, scheduler)
        monitor.set_telegram_bot(telegram_bot)
        
        if telegram_bot.enabled:
            # 在单独线程中启动 Bot
            bot_thread = threading.Thread(target=run_telegram_bot, args=(telegram_bot,), daemon=True)
            bot_thread.start()
            logger.info("✅ Telegram Bot 已在后台启动")
        else:
            logger.warning("⚠️ Telegram Bot 初始化失败")
    else:
        logger.info("ℹ️ Telegram Bot 未启用")
    
    if args.list:
        print("\n📋 服务器列表：\n")
        servers = hetzner.get_servers()
        for server in servers:
            print(f"  ID: {server['id']}")
            print(f"  名称: {server['name']}")
            print(f"  状态: {server['status']}")
            print(f"  IP: {server['public_net']['ipv4']['ip']}")
            print(f"  类型: {server['server_type']['name']}")
            print("-" * 50)
        return
    
    if args.check_traffic:
        server = hetzner.get_server(args.check_traffic)
        if not server:
            print(f"❌ 服务器 ID {args.check_traffic} 不存在")
            return
        
        print(f"\n📊 服务器 {server['name']} 流量统计：\n")
        traffic = hetzner.calculate_traffic(args.check_traffic)
        print(f"  入站流量: {traffic['inbound']:.2f} GB")
        print(f"  出站流量: {traffic['outbound']:.2f} GB")
        print(f"  总流量: {traffic['total']:.2f} GB")
        print(f"  流量限制: {config['traffic']['limit_gb']} GB")
        usage = (traffic['total'] / config['traffic']['limit_gb']) * 100
        print(f"  使用率: {usage:.2f}%")
        if traffic['total'] > config['traffic']['limit_gb']:
            print("\n  ⚠️  警告：流量已超限！")
        return
    
    scheduler.load_tasks()
    
    if args.once:
        logger.info("运行模式：单次检查")
        summary = monitor.monitor(dry_run=args.dry_run)
        if summary['warning_servers']:
            notifier.notify_traffic_warning(summary['warning_servers'])
        if summary['actions_taken']:
            notifier.notify_traffic_exceeded(summary['actions_taken'])
        logger.info("单次检查完成")
        return
    
    logger.info("运行模式：持续监控")
    check_interval = config['traffic']['check_interval']
    logger.info(f"流量检查间隔: {check_interval} 分钟")
    
    try:
        while True:
            summary = monitor.monitor(dry_run=args.dry_run)
            if summary['warning_servers']:
                notifier.notify_traffic_warning(summary['warning_servers'])
            if summary['actions_taken']:
                notifier.notify_traffic_exceeded(summary['actions_taken'])
            scheduler.run_pending()
            logger.info(f"等待 {check_interval} 分钟后进行下次检查...")
            time.sleep(check_interval * 60)
    except KeyboardInterrupt:
        logger.info("\n收到中断信号，正在退出...")
        logger.info("程序已停止")


if __name__ == '__main__':
    main()
