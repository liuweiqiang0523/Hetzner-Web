import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
import time


class HetznerManager:
    BASE_URL = "https://api.hetzner.cloud/v1"
    
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        self.logger = logging.getLogger(__name__)
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API 请求失败: {e}")
            raise
    
    def get_servers(self) -> List[Dict]:
        self.logger.info("获取服务器列表...")
        response = self._request("GET", "servers")
        return response.get("servers", [])
    
    def get_server(self, server_id: int) -> Optional[Dict]:
        try:
            response = self._request("GET", f"servers/{server_id}")
            return response.get("server")
        except Exception as e:
            self.logger.error(f"获取服务器 {server_id} 信息失败: {e}")
            return None
    
    def get_server_metrics(
        self,
        server_id: int,
        metric_type: str = "network",
        start: datetime = None,
        end: datetime = None,
    ) -> Dict:
        if not start:
            start = datetime.now(timezone.utc) - timedelta(hours=1)
        if not end:
            end = datetime.now(timezone.utc)

        # Ensure timezone-aware UTC and cap range to 30 days (Hetzner API limit).
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        if end < start:
            start, end = end, start
        max_range = timedelta(days=30)
        if end - start > max_range:
            start = end - max_range
        
        params = {
            "type": metric_type,
            "start": start.isoformat(),
            "end": end.isoformat()
        }
        
        try:
            response = self._request("GET", f"servers/{server_id}/metrics", params=params)
            return response.get("metrics", {})
        except Exception as e:
            self.logger.error(f"获取服务器 {server_id} 指标失败: {e}")
            return {}
    
    def _sum_series_gb(self, time_series: Dict, key: str) -> float:
        values = time_series.get(key, {}).get("values", [])
        if not values:
            return 0.0
        return sum(float(v[1]) for v in values) / (1024**3)

    def calculate_traffic(self, server_id: int, days: int = 30) -> Dict:
        end = datetime.now(timezone.utc)
        days = min(days, 30)
        start = end - timedelta(days=days)
        metrics = self.get_server_metrics(server_id, "network", start, end)

        inbound = 0.0
        outbound = 0.0
        if metrics:
            time_series = metrics.get("time_series", {})
            inbound = self._sum_series_gb(time_series, "network.0.bandwidth.in")
            outbound = self._sum_series_gb(time_series, "network.0.bandwidth.out")

        server_detail = self.get_server(server_id)
        inbound_bytes = None
        outbound_bytes = None
        if server_detail:
            inbound_bytes = server_detail.get("ingoing_traffic")
            outbound_bytes = server_detail.get("outgoing_traffic")

        return {
            "inbound": round(inbound, 2),
            "outbound": round(outbound, 2),
            "total": round(inbound + outbound, 2),
            "inbound_bytes": inbound_bytes,
            "outbound_bytes": outbound_bytes,
        }

    def get_today_traffic(self, server_id: int) -> Dict:
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=1)
        metrics = self.get_server_metrics(server_id, "network", start, end)
        if not metrics:
            return {"inbound": 0, "outbound": 0, "total": 0}

        time_series = metrics.get("time_series", {})
        inbound = self._sum_series_gb(time_series, "network.0.bandwidth.in")
        outbound = self._sum_series_gb(time_series, "network.0.bandwidth.out")

        return {
            "inbound": round(inbound, 2),
            "outbound": round(outbound, 2),
            "total": round(inbound + outbound, 2),
        }
    
    def shutdown_server(self, server_id: int) -> bool:
        try:
            self.logger.info(f"正在关闭服务器 {server_id}...")
            self._request("POST", f"servers/{server_id}/actions/shutdown")
            self.logger.info(f"服务器 {server_id} 关闭成功")
            return True
        except Exception as e:
            self.logger.error(f"关闭服务器 {server_id} 失败: {e}")
            return False
    
    def poweron_server(self, server_id: int) -> bool:
        try:
            self.logger.info(f"正在开启服务器 {server_id}...")
            self._request("POST", f"servers/{server_id}/actions/poweron")
            self.logger.info(f"服务器 {server_id} 开启成功")
            return True
        except Exception as e:
            self.logger.error(f"开启服务器 {server_id} 失败: {e}")
            return False
    
    def reboot_server(self, server_id: int) -> bool:
        try:
            self.logger.info(f"正在重启服务器 {server_id}...")
            self._request("POST", f"servers/{server_id}/actions/reboot")
            self.logger.info(f"服务器 {server_id} 重启成功")
            return True
        except Exception as e:
            self.logger.error(f"重启服务器 {server_id} 失败: {e}")
            return False
    
    def delete_server(self, server_id: int) -> bool:
        try:
            self.logger.warning(f"正在删除服务器 {server_id}...")
            self._request("DELETE", f"servers/{server_id}")
            self.logger.warning(f"服务器 {server_id} 已删除")
            return True
        except Exception as e:
            self.logger.error(f"删除服务器 {server_id} 失败: {e}")
            return False

    def get_snapshots(self) -> List[Dict]:
        try:
            response = self._request("GET", "images", params={"type": "snapshot"})
            return response.get("images", [])
        except Exception as e:
            self.logger.error(f"获取快照列表失败: {e}")
            return []

    def create_snapshot(self, server_id: int, description: str = "") -> Optional[Dict]:
        try:
            payload = {"type": "snapshot"}
            if description:
                payload["description"] = description
            response = self._request("POST", f"servers/{server_id}/actions/create_image", json=payload)
            image = response.get("image")
            self.logger.info(f"服务器 {server_id} 快照创建已触发")
            return image
        except Exception as e:
            self.logger.error(f"创建服务器 {server_id} 快照失败: {e}")
            return None

    def _parse_iso_datetime(self, value: str) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            return None

    def get_latest_snapshot_for_server(self, server_id: int) -> Optional[Dict]:
        snapshots = self.get_snapshots()
        if not snapshots:
            return None

        candidates = []
        for snapshot in snapshots:
            created_from = snapshot.get("created_from") or {}
            if created_from.get("id") == server_id:
                candidates.append(snapshot)

        if not candidates:
            return None

        def sort_key(s: Dict):
            created = self._parse_iso_datetime(s.get("created"))
            return created or datetime.min

        return max(candidates, key=sort_key)

    def rebuild_server_from_snapshot(self, server_id: int) -> bool:
        try:
            snapshot = self.get_latest_snapshot_for_server(server_id)
            if not snapshot:
                self.logger.error(f"未找到服务器 {server_id} 的快照，无法重建")
                return False

            snapshot_id = snapshot.get("id")
            snapshot_name = snapshot.get("name", "")
            self.logger.warning(
                f"正在重建服务器 {server_id}，使用快照 {snapshot_id} {snapshot_name}"
            )
            self._request(
                "POST",
                f"servers/{server_id}/actions/rebuild",
                json={"image": snapshot_id},
            )
            self.logger.warning(f"服务器 {server_id} 重建已触发")
            return True
        except Exception as e:
            self.logger.error(f"重建服务器 {server_id} 失败: {e}")
            return False

    def create_server_from_snapshot(
        self,
        name: str,
        server_type: str,
        location: str,
        snapshot_id: int,
        ssh_keys: Optional[List[int]] = None,
    ) -> Optional[Dict]:
        if not server_type or not location:
            self.logger.error("创建服务器失败: server_type/location 不能为空")
            return None

        payload = {
            "name": name,
            "server_type": server_type,
            "location": location,
            "image": snapshot_id,
        }
        if ssh_keys:
            payload["ssh_keys"] = ssh_keys

        try:
            response = self._request("POST", "servers", json=payload)
            return response.get("server")
        except Exception as e:
            self.logger.error(f"创建服务器失败: {e}")
            return None

    def _generate_name(self, name_prefix: Optional[str]) -> str:
        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        prefix = name_prefix or "auto-"
        return f"{prefix}{ts}"

    def delete_and_recreate_from_snapshot(
        self,
        server_id: int,
        server_type: str,
        location: str,
        ssh_keys: Optional[List[int]] = None,
        name_prefix: Optional[str] = None,
        use_original_name: bool = True,
        fallbacks: Optional[List[Dict]] = None,
    ) -> Dict:
        try:
            server = self.get_server(server_id)
            if not server:
                self.logger.error(f"未找到服务器 {server_id}，无法重建")
                return {"success": False, "error": "server_not_found"}

            snapshot = self.get_latest_snapshot_for_server(server_id)
            if not snapshot:
                self.logger.error(f"未找到服务器 {server_id} 的快照，无法重建")
                return {"success": False, "error": "snapshot_not_found"}

            snapshot_id = snapshot.get("id")
            original_name = server.get("name") or ""
            name = original_name if use_original_name and original_name else self._generate_name(name_prefix)

            self.logger.warning(
                f"执行删除并重建: {original_name or server_id} -> 快照 {snapshot_id}"
            )

            if not self.delete_server(server_id):
                return {"success": False, "error": "delete_failed"}

            # Give the API a moment to finish delete before creating a new server.
            time.sleep(2)

            created = self.create_server_from_snapshot(
                name=name,
                server_type=server_type,
                location=location,
                snapshot_id=snapshot_id,
                ssh_keys=ssh_keys,
            )
            if not created and not name_prefix:
                fallback_name = self._generate_name(name_prefix)
                created = self.create_server_from_snapshot(
                    name=fallback_name,
                    server_type=server_type,
                    location=location,
                    snapshot_id=snapshot_id,
                    ssh_keys=ssh_keys,
                )

            if created:
                self.logger.warning(f"服务器已创建: {created.get('id')} {created.get('name')}")
                return {
                    "success": True,
                    "new_server_id": created.get("id"),
                    "new_ip": (created.get("public_net") or {}).get("ipv4", {}).get("ip"),
                    "snapshot_id": snapshot_id,
                }

            fallback_list = fallbacks or []
            for fallback in fallback_list:
                fb_type = fallback.get("server_type")
                fb_snapshot_id = fallback.get("snapshot_id")
                if not (fb_type and fb_snapshot_id):
                    continue
                self.logger.warning(
                    f"主型号创建失败，尝试备用型号: {fb_type} 快照 {fb_snapshot_id}"
                )
                created = self.create_server_from_snapshot(
                    name=name,
                    server_type=fb_type,
                    location=location,
                    snapshot_id=int(fb_snapshot_id),
                    ssh_keys=ssh_keys,
                )
                if created:
                    self.logger.warning(f"服务器已创建: {created.get('id')} {created.get('name')}")
                    return {
                        "success": True,
                        "new_server_id": created.get("id"),
                        "new_ip": (created.get("public_net") or {}).get("ipv4", {}).get("ip"),
                        "snapshot_id": fb_snapshot_id,
                        "server_type": fb_type,
                    }

            self.logger.error("删除后创建服务器失败")
            return {"success": False, "error": "create_failed"}
        except Exception as e:
            self.logger.error(f"删除并重建服务器 {server_id} 失败: {e}")
            return {"success": False, "error": str(e)}

    def delete_and_recreate_from_snapshot_id(
        self,
        server_id: int,
        snapshot_id: int,
        server_type: str,
        location: str,
        ssh_keys: Optional[List[int]] = None,
        name_prefix: Optional[str] = None,
        use_original_name: bool = True,
        fallbacks: Optional[List[Dict]] = None,
    ) -> Dict:
        try:
            server = self.get_server(server_id)
            if not server:
                self.logger.error(f"未找到服务器 {server_id}，无法重建")
                return {"success": False, "error": "server_not_found"}

            original_name = server.get("name") or ""
            name = original_name if use_original_name and original_name else self._generate_name(name_prefix)

            self.logger.warning(
                f"执行删除并重建: {original_name or server_id} -> 快照 {snapshot_id}"
            )

            if not self.delete_server(server_id):
                return {"success": False, "error": "delete_failed"}

            time.sleep(2)

            created = self.create_server_from_snapshot(
                name=name,
                server_type=server_type,
                location=location,
                snapshot_id=snapshot_id,
                ssh_keys=ssh_keys,
            )
            if not created and not name_prefix:
                fallback_name = self._generate_name(name_prefix)
                created = self.create_server_from_snapshot(
                    name=fallback_name,
                    server_type=server_type,
                    location=location,
                    snapshot_id=snapshot_id,
                    ssh_keys=ssh_keys,
                )

            if created:
                self.logger.warning(f"服务器已创建: {created.get('id')} {created.get('name')}")
                return {
                    "success": True,
                    "new_server_id": created.get("id"),
                    "new_ip": (created.get("public_net") or {}).get("ipv4", {}).get("ip"),
                    "snapshot_id": snapshot_id,
                }

            fallback_list = fallbacks or []
            for fallback in fallback_list:
                fb_type = fallback.get("server_type")
                fb_snapshot_id = fallback.get("snapshot_id")
                if not (fb_type and fb_snapshot_id):
                    continue
                self.logger.warning(
                    f"主型号创建失败，尝试备用型号: {fb_type} 快照 {fb_snapshot_id}"
                )
                created = self.create_server_from_snapshot(
                    name=name,
                    server_type=fb_type,
                    location=location,
                    snapshot_id=int(fb_snapshot_id),
                    ssh_keys=ssh_keys,
                )
                if created:
                    self.logger.warning(f"服务器已创建: {created.get('id')} {created.get('name')}")
                    return {
                        "success": True,
                        "new_server_id": created.get("id"),
                        "new_ip": (created.get("public_net") or {}).get("ipv4", {}).get("ip"),
                        "snapshot_id": fb_snapshot_id,
                        "server_type": fb_type,
                    }

            self.logger.error("删除后创建服务器失败")
            return {"success": False, "error": "create_failed"}
        except Exception as e:
            self.logger.error(f"删除并重建服务器 {server_id} 失败: {e}")
            return {"success": False, "error": str(e)}

    CF_API_BASE = "https://api.cloudflare.com/client/v4"

    def update_cloudflare_a_record(
        self, api_token: str, zone_id: str, record_name: str, ip: str, attempts: int = 3
    ) -> Dict:
        last_error = None
        for _ in range(attempts):
            try:
                headers = {
                    "Authorization": f"Bearer {api_token}",
                    "Content-Type": "application/json",
                }
                list_url = f"{self.CF_API_BASE}/zones/{zone_id}/dns_records"
                params = {"type": "A", "name": record_name}
                resp = requests.get(list_url, headers=headers, params=params, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                records = data.get("result", [])
                if not records:
                    return {"success": False, "error": "DNS记录不存在"}
                record = records[0]
                record_id = record.get("id")
                update_url = f"{self.CF_API_BASE}/zones/{zone_id}/dns_records/{record_id}"
                payload = {
                    "type": "A",
                    "name": record_name,
                    "content": ip,
                    "ttl": record.get("ttl", 1),
                    "proxied": record.get("proxied", False),
                }
                upd = requests.put(update_url, headers=headers, json=payload, timeout=15)
                upd.raise_for_status()
                return {"success": True}
            except Exception as e:
                last_error = e
                time.sleep(3)
        return {"success": False, "error": str(last_error)}
