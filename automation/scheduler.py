"""任务调度器"""
import logging
import time
from typing import Dict, List, Optional
import yaml

try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False
    schedule = None


class TaskScheduler:
    def __init__(self, hetzner, config):
        self.hetzner = hetzner
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._enabled = config['scheduler'].get('enabled', False)

        if not SCHEDULE_AVAILABLE:
            self.logger.warning("schedule 模块未安装，定时功能不可用")

    def _config_path(self) -> str:
        return self.config.get('_config_path', 'config.yaml')

    def _save_config(self) -> None:
        path = self._config_path()
        try:
            with open(path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(self.config, f, sort_keys=False, allow_unicode=True)
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")

    def is_enabled(self):
        return self._enabled

    def enable(self):
        self._enabled = True
        self.config['scheduler']['enabled'] = True
        self._save_config()
        self.logger.info("调度器已启用")

    def disable(self):
        self._enabled = False
        self.config['scheduler']['enabled'] = False
        self._save_config()
        self.logger.info("调度器已禁用")

    def _clear_jobs(self):
        if schedule:
            schedule.clear()

    def _record_name(self, record_map: Dict, old_id: str) -> Optional[str]:
        name = record_map.get(str(old_id))
        if not name:
            return None
        return name.split('.')[0]

    def _update_config_mapping(self, old_id: int, new_id: int) -> None:
        snapshot_map = self.config.get('snapshot_map', {})
        old_snapshot_key = old_id if old_id in snapshot_map else str(old_id)
        if old_snapshot_key in snapshot_map:
            new_snapshot_key = new_id if isinstance(old_snapshot_key, int) else str(new_id)
            snapshot_map[new_snapshot_key] = snapshot_map[old_snapshot_key]
            snapshot_map.pop(old_snapshot_key, None)
            self.config['snapshot_map'] = snapshot_map

        cloudflare = self.config.get('cloudflare', {})
        record_map = cloudflare.get('record_map', {})
        old_record_key = str(old_id) if str(old_id) in record_map else old_id
        if old_record_key in record_map:
            new_record_key = str(new_id) if isinstance(old_record_key, str) else new_id
            record_map[new_record_key] = record_map[old_record_key]
            record_map.pop(old_record_key, None)
            cloudflare['record_map'] = record_map
            self.config['cloudflare'] = cloudflare

        self._save_config()

    def _update_dns(self, old_id: int, new_ip: Optional[str]) -> None:
        if not new_ip:
            return
        cf_cfg = self.config.get('cloudflare', {})
        api_token = cf_cfg.get('api_token')
        zone_id = cf_cfg.get('zone_id')
        record_map = cf_cfg.get('record_map', {})
        record_name = record_map.get(str(old_id))
        if not (api_token and zone_id and record_name):
            return
        res = self.hetzner.update_cloudflare_a_record(api_token, zone_id, record_name, new_ip)
        if res.get('success'):
            self.logger.info(f"DNS 已更新: {record_name} -> {new_ip}")
        else:
            self.logger.error(f"DNS 更新失败: {record_name} ({res.get('error')})")

    def delete_all_servers(self):
        servers = self.hetzner.get_servers()
        whitelist_ids = set(self.config.get('whitelist', {}).get('server_ids', []))
        whitelist_names = set(self.config.get('whitelist', {}).get('server_names', []))

        for server in servers:
            if server['id'] in whitelist_ids or server['name'] in whitelist_names:
                continue
            self.hetzner.delete_server(server['id'])
            time.sleep(1)

    def create_from_snapshot_map(self):
        snapshot_map = self.config.get('snapshot_map', {})
        if not snapshot_map:
            self.logger.warning("snapshot_map 为空，无法创建服务器")
            return

        template = self.config.get('server_template', {})
        server_type = template.get('server_type')
        location = template.get('location')
        ssh_keys = template.get('ssh_keys', [])
        name_prefix = template.get('name_prefix')

        cloudflare = self.config.get('cloudflare', {})
        record_map = cloudflare.get('record_map', {})

        for old_id, snapshot_id in snapshot_map.items():
            name = None
            if record_map:
                name = self._record_name(record_map, old_id)
            if not name:
                name = f"{name_prefix or 'auto-'}{old_id}"

            created = self.hetzner.create_server_from_snapshot(
                name=name,
                server_type=server_type,
                location=location,
                snapshot_id=int(snapshot_id),
                ssh_keys=ssh_keys,
            )
            if not created:
                self.logger.error(f"创建服务器失败: snapshot {snapshot_id}")
                continue

            new_id = created.get('id')
            new_ip = (created.get('public_net') or {}).get('ipv4', {}).get('ip')
            if new_id:
                self._update_config_mapping(int(old_id), int(new_id))
                self._update_dns(int(old_id), new_ip)

    def _run_task(self, action: str):
        if action == "delete_all":
            self.logger.info("执行定时任务: delete_all")
            self.delete_all_servers()
        elif action == "create_from_snapshots":
            self.logger.info("执行定时任务: create_from_snapshots")
            self.create_from_snapshot_map()
        else:
            self.logger.error(f"未知定时任务: {action}")

    def load_tasks(self):
        if not self._enabled:
            self.logger.info("定时任务调度已禁用")
            self._clear_jobs()
            return

        if not SCHEDULE_AVAILABLE:
            self.logger.warning("schedule 模块未安装，无法加载定时任务")
            return

        self._clear_jobs()
        tasks = self.config['scheduler'].get('tasks', [])
        count = 0
        for task in tasks:
            action = task.get('action')
            times = task.get('times', [])
            for at_time in times:
                schedule.every().day.at(at_time).do(self._run_task, action=action)
                count += 1
        self.logger.info(f"已加载 {count} 个定时任务")

    def run_pending(self):
        if SCHEDULE_AVAILABLE and schedule:
            schedule.run_pending()

    def get_next_run(self) -> str:
        if not SCHEDULE_AVAILABLE:
            return "定时功能不可用"

        jobs = schedule.get_jobs() if schedule else []
        if not jobs:
            return "无待执行任务"

        next_run = min(job.next_run for job in jobs)
        return next_run.strftime("%Y-%m-%d %H:%M:%S")
