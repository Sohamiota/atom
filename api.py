import json
from typing import Any, Dict, Optional

import requests


class HealthAPIClient:
    def __init__(self,
                rpc_url: str = "https://log.sli.ke/rpc",
                auth_token: str = "18n9o69lklg6gkuo6uk96kglgoogk6l6",
                service_id: str = "4pc9typi"):
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
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None
    
    def send_health_data(self, health_payload: Dict[str, Any]) -> Optional[requests.Response]:
        if "params" in health_payload and isinstance(health_payload["params"], dict):
            health_payload["params"]["service"] = self.service_id
        response = self.make_request(health_payload)
        if response and response.status_code == 200:
            print("Health data sent to API")
        else:
            print("Failed to send health data to API")
        return response
    
    def get_alerts(self) -> Optional[requests.Response]:
        payload = {
            "jsonrpc": "2.0",
            "method": "service.alerts",
            "params": {
                "service": self.service_id
            }
        }
        response = self.make_request(payload)
        if response and response.status_code == 200:
            print("Alerts fetched from API")
        else:
            print("Failed to fetch alerts from API")
        return response
    
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
        response = self.make_request(payload)
        if response and response.status_code == 200:
            print("Notification sent to API")
        else:
            print("Failed to send notification to API")
        return response
    
    def process_alerts(self, alert_response: Optional[requests.Response]) -> str:
        try:
            if alert_response and alert_response.status_code == 200:
                alert_data = alert_response.json()
                alerts = alert_data.get("result", {}).get("alerts", [])
                alert_count = len(alerts)
                message = "No alerts detected" if alert_count == 0 else f"Alerts detected: {alert_count}"
                print(message)
                return message
            else:
                print("Alert status unknown")
                return "Alert status unknown"
        except Exception:
            print("Alert status unknown")
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


if __name__ == "__main__":
    api_client = HealthAPIClient()
    sample_health_data = {
        "jsonrpc": "2.0",
        "method": "service.health",
        "params": {
            "atom": 1,
            "name": "AtomClient",
            "env": "production",
            "project": "HealthMonitoring",
            "stype": "monitor"
        }
    }
    results = api_client.health_check_cycle(sample_health_data)
    print(f"Health API Status: {results['health_response'].status_code if results['health_response'] else 'Failed'}")
    print(f"Alert API Status: {results['alert_response'].status_code if results['alert_response'] else 'Failed'}")
    print(f"Notify API Status: {results['notify_response'].status_code if results['notify_response'] else 'Failed'}")
