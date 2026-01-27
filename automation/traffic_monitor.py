import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
import yaml
from hetzner_manager import HetznerManager


class TrafficMonitor:
    def __init__(self, hetzner: HetznerManager, config: Dict, telegram_bot: Optional[object] = None):
        self.hetzner = hetzner
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.telegram_bot = telegram_bot
        
        self.traffic_limit = config['traffic']['limit_gb']
        self.exceed_action = config['traffic']['exceed_action']
        self.warning_thresholds = config['traffic']['warning_thresholds']
        self.whitelist_ids = config['whitelist']['server_ids']
        self.whitelist_names = config['whitelist']['server_names']
        self._threshold_state_path = Path("/opt/hetzner-web/threshold_state.json")

    def set_telegram_bot(self, telegram_bot: Optional[object]):
        self.telegram_bot = telegram_bot

    def _load_threshold_state(self) -> Dict[str, int]:
        if not self._threshold_state_path.exists():
            return {}
        try:
            return json.loads(self._threshold_state_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_threshold_state(self, state: Dict[str, int]) -> None:
        try:
            self._threshold_state_path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            self.logger.error(f"保存阈值状态失败: {e}")

    def reset_server_thresholds(self, server_id: int) -> None:
        state = self._load_threshold_state()
        state[str(server_id)] = 0
        self._save_threshold_state(state)

    def _update_threshold_on_rebuild(self, old_id: int, new_id: Optional[int]) -> None:
        state = self._load_threshold_state()
        if str(old_id) in state:
            state.pop(str(old_id), None)
        if new_id is not None:
            state[str(new_id)] = 0
        self._save_threshold_state(state)

    def _config_path(self) -> str:
        return self.config.get('_config_path', 'config.yaml')

    def _update_config_mapping(self, old_id: int, new_id: int) -> None:
        path = self._config_path()
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
        except Exception as e:
            self.logger.error(f"读取配置失败: {e}")
            return

        changed = False
        snapshot_map = data.get('snapshot_map', {}) or {}
        old_snapshot_key = old_id if old_id in snapshot_map else str(old_id)
        if old_snapshot_key in snapshot_map:
            new_snapshot_key = new_id if isinstance(old_snapshot_key, int) else str(new_id)
            snapshot_map[new_snapshot_key] = snapshot_map[old_snapshot_key]
            snapshot_map.pop(old_snapshot_key, None)
            data['snapshot_map'] = snapshot_map
            changed = True

        cloudflare = data.get('cloudflare', {}) or {}
        record_map = cloudflare.get('record_map', {}) or {}
        old_record_key = str(old_id) if str(old_id) in record_map else old_id
        if old_record_key in record_map:
            new_record_key = str(new_id) if isinstance(old_record_key, str) else new_id
            record_map[new_record_key] = record_map[old_record_key]
            record_map.pop(old_record_key, None)
            cloudflare['record_map'] = record_map
            data['cloudflare'] = cloudflare
            changed = True

        if not changed:
            return

        try:
            with open(path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
            # Keep in-memory config aligned.
            self.config.update(data)
        except Exception as e:
            self.logger.error(f"更新配置映射失败: {e}")

    def _update_dns_after_rebuild(
        self,
        old_id: int,
        new_ip: Optional[str],
        new_id: Optional[int] = None,
    ) -> None:
        if not new_ip:
            return
        cf_cfg = self.config.get('cloudflare', {})
        api_token = cf_cfg.get('api_token')
        zone_id = cf_cfg.get('zone_id')
        record_map = cf_cfg.get('record_map', {}) or {}
        record_name = record_map.get(str(old_id))
        if not record_name and new_id is not None:
            record_name = record_map.get(str(new_id))
        if not (api_token and zone_id and record_name):
            return
        res = self.hetzner.update_cloudflare_a_record(api_token, zone_id, record_name, new_ip)
        if res.get('success'):
            if self.telegram_bot:
                try:
                    self.telegram_bot.send_dns_update_result(record_name, new_ip, True, None)
                except Exception:
                    pass
        else:
            if self.telegram_bot:
                try:
                    self.telegram_bot.send_dns_update_result(record_name, new_ip, False, res.get('error'))
                except Exception:
                    pass

    def handle_rebuild_success(self, old_id: int, result: Dict) -> None:
        new_id = result.get('new_server_id')
        new_ip = result.get('new_ip')
        self._update_dns_after_rebuild(old_id, new_ip, new_id if isinstance(new_id, int) else None)
        if isinstance(new_id, int):
            self._update_config_mapping(old_id, new_id)
        self._update_threshold_on_rebuild(old_id, new_id if isinstance(new_id, int) else None)
    
    def is_whitelisted(self, server: Dict) -> bool:
        server_id = server['id']
        server_name = server['name']
        return (server_id in self.whitelist_ids or server_name in self.whitelist_names)
    
    def check_server_traffic(self, server: Dict) -> Dict:
        server_id = server['id']
        server_name = server['name']
        
        self.logger.info(f"检查服务器 {server_name} (ID: {server_id}) 的流量...")
        
        traffic = self.hetzner.calculate_traffic(server_id, days=30)
        outbound_bytes = traffic.get('outbound_bytes')
        if outbound_bytes is not None:
            total_traffic = float(outbound_bytes) / (1024**3)
            usage_percent = (total_traffic / self.traffic_limit) * 100
        else:
            total_traffic = traffic['total']
            usage_percent = (total_traffic / self.traffic_limit) * 100
        
        state = self._load_threshold_state()
        last_threshold = int(state.get(str(server_id), 0))
        thresholds = sorted(self.warning_thresholds)
        current_threshold = 0
        for threshold in thresholds:
            if usage_percent >= threshold:
                current_threshold = threshold

        new_threshold = None
        if current_threshold > last_threshold:
            new_threshold = current_threshold
            state[str(server_id)] = current_threshold
            self._save_threshold_state(state)

        result = {
            'server_id': server_id,
            'server_name': server_name,
            'traffic': traffic,
            'limit': self.traffic_limit,
            'usage_percent': round(usage_percent, 2),
            'exceeded': total_traffic > self.traffic_limit,
            'whitelisted': self.is_whitelisted(server),
            'warnings': [],
            'new_threshold': new_threshold,
        }
        
        for threshold in sorted(self.warning_thresholds):
            if usage_percent >= threshold and usage_percent < threshold + 5:
                result['warnings'].append(threshold)
        
        self.logger.info(
            f"服务器 {server_name}: 流量 {total_traffic:.2f}GB / {self.traffic_limit}GB ({usage_percent:.2f}%)"
        )
        
        return result
    
    def check_all_servers(self) -> List[Dict]:
        servers = self.hetzner.get_servers()
        results = []
        
        for server in servers:
            try:
                result = self.check_server_traffic(server)
                results.append(result)
            except Exception as e:
                self.logger.error(f"检查服务器 {server['name']} 流量时出错: {e}")
        
        return results
    
    def handle_exceeded_server(self, result: Dict) -> bool:
        server_id = result['server_id']
        server_name = result['server_name']
        
        if result['whitelisted']:
            self.logger.info(f"服务器 {server_name} 在白名单中，跳过处理")
            return False
        
        if not result['exceeded']:
            return False
        
        self.logger.warning(
            f"服务器 {server_name} 流量超限: {result['traffic']['total']:.2f}GB / {result['limit']}GB"
        )
        
        action = self.exceed_action.lower()
        
        if action == 'delete':
            self.logger.warning(f"执行删除操作: {server_name}")
            return self.hetzner.delete_server(server_id)
        elif action == 'shutdown':
            self.logger.warning(f"执行关机操作: {server_name}")
            return self.hetzner.shutdown_server(server_id)
        elif action == 'rebuild':
            self.logger.warning(f"执行重建操作: {server_name}")
            return self.hetzner.rebuild_server_from_snapshot(server_id)
        elif action == 'delete_rebuild':
            self.logger.warning(f"执行删除后重建操作: {server_name}")
            template = self.config.get('server_template', {})
            server_type = template.get('server_type')
            location = template.get('location')
            ssh_keys = template.get('ssh_keys', [])
            name_prefix = template.get('name_prefix')
            use_original_name = template.get('use_original_name', True)
            snapshot_map = self.config.get('snapshot_map', {})
            override_snapshot_id = snapshot_map.get(server_id)

            if not server_type or not location:
                self.logger.error("server_template 未配置 server_type/location，无法重建")
                return False
            if override_snapshot_id:
                result = self.hetzner.delete_and_recreate_from_snapshot_id(
                    server_id=server_id,
                    snapshot_id=override_snapshot_id,
                    server_type=server_type,
                    location=location,
                    ssh_keys=ssh_keys,
                    name_prefix=name_prefix,
                    use_original_name=use_original_name,
                )
            else:
                result = self.hetzner.delete_and_recreate_from_snapshot(
                    server_id=server_id,
                    server_type=server_type,
                    location=location,
                    ssh_keys=ssh_keys,
                    name_prefix=name_prefix,
                    use_original_name=use_original_name,
                )

            if isinstance(result, dict):
                if result.get("success") and self.telegram_bot:
                    try:
                        self.telegram_bot.send_rebuild_success_notification(result)
                    except Exception:
                        pass
                    self.handle_rebuild_success(server_id, result)
                elif not result.get("success") and self.telegram_bot:
                    try:
                        self.telegram_bot.send_rebuild_failed_notification(result)
                    except Exception:
                        pass
                return bool(result.get("success"))

            return bool(result)
        elif action == 'notify':
            self.logger.warning(f"仅通知，不执行操作: {server_name}")
            return True
        else:
            self.logger.error(f"未知的超限操作: {action}")
            return False
    
    def monitor(self) -> Dict:
        self.logger.info("=" * 60)
        self.logger.info("开始流量监控...")
        
        results = self.check_all_servers()
        
        summary = {
            'total_servers': len(results),
            'exceeded_servers': [],
            'warning_servers': [],
            'normal_servers': [],
            'actions_taken': []
        }
        
        for result in results:
            if result['exceeded']:
                summary['exceeded_servers'].append(result)
                if self.telegram_bot and result.get('new_threshold') is not None:
                    try:
                        self.telegram_bot.send_traffic_notification(result)
                    except Exception:
                        pass
                if self.handle_exceeded_server(result):
                    summary['actions_taken'].append({
                        'server': result['server_name'],
                        'action': self.exceed_action,
                        'traffic': result['traffic']['total']
                    })
                if self.telegram_bot:
                    try:
                        self.telegram_bot.send_exceed_notification(result)
                    except Exception:
                        pass
            elif result['warnings']:
                summary['warning_servers'].append(result)
                if self.telegram_bot and result.get('new_threshold') is not None:
                    try:
                        self.telegram_bot.send_traffic_notification(result)
                    except Exception:
                        pass
            else:
                summary['normal_servers'].append(result)
        
        self.logger.info(
            f"监控完成: 总计 {summary['total_servers']} 台服务器, "
            f"超限 {len(summary['exceeded_servers'])} 台, "
            f"警告 {len(summary['warning_servers'])} 台"
        )
        self.logger.info("=" * 60)
        
        return summary
