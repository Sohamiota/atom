import json
from typing import Any, Dict, Optional

import config
import requests


class HealthAPIClient:
    def __init__(self,
                rpc_url: str = config.RPC_URL,
                auth_token: str = config.AUTH_TOKEN,
                service_id: str = config.SERVICE_ID):
        self.rpc_url = rpc_url
        self.service_id = service_id
        self.session = requests.Session()
        self.session.headers.update({
            "token": auth_token,
            "Content-Type": "application/json"
        })

    def make_request(self, payload: Dict[str, Any]) -> Optional[requests.Response]:
        try:
            response = self.session.post(self.rpc_url, json=payload)
            return response
        except requests.RequestException:
            return None

    def send_health_data(self, health_payload: Dict[str, Any]) -> Optional[requests.Response]:
        if "params" in health_payload and isinstance(health_payload["params"], dict):
            health_payload["params"]["service"] = self.service_id
        return self.make_request(health_payload)

    def get_alerts(self) -> Optional[requests.Response]:
        payload = {
            "jsonrpc": "2.0",
            "method": "service.alerts",
            "params": {
                "service": self.service_id
            }
        }
        return self.make_request(payload)

    def send_notification(self, message: str, tags: Optional[list] = None) -> Optional[requests.Response]:
        payload = {
            "jsonrpc": "2.0",
            "method": "service.notify",
            "params": {
                "service": self.service_id,
                "msg": message,
                "tags": tags or ["health", "monitoring"]
            }
        }
        return self.make_request(payload)

    def process_alerts(self, alert_response: Optional[requests.Response]) -> str:
        try:
            if alert_response and alert_response.status_code == 200:
                alert_data = alert_response.json()
                alerts = alert_data.get("result", {}).get("alerts", [])
                alert_count = len(alerts)
                return "No alerts detected" if alert_count == 0 else f"Alerts detected: {alert_count}"
            else:
                return "Alert status unknown"
        except Exception:
            return "Alert status unknown"

    def health_check_cycle(self, health_data: Dict[str, Any]) -> Dict[str, Optional[requests.Response]]:
        health_response = self.send_health_data(health_data)
        alert_response = self.get_alerts()
        message = self.process_alerts(alert_response)
        notify_response = self.send_notification(message)
        return {
            "health_response": health_response,
            "alert_response": alert_response,
            "notify_response": notify_response
        }