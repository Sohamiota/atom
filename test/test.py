import json

import requests

from atom.monitor import HealthMonitor

RPC_URL = "https://log.sli.ke/rpc"
AUTH_TOKEN = "18n9o69lklg6gkuo6uk96kglgoogk6l6"

def send_health_data():
    monitor = HealthMonitor()
    payload = monitor.get_health_data()

    alerts = monitor.check_anomalies(payload)

    payload["params"]["alerts"] = alerts
    payload["params"]["service"] = "4pc9typi"

    headers = {
        "token": AUTH_TOKEN,
        "Content-Type": "application/json"
    }

    
    print(f"Payload (service.health): {json.dumps(payload, indent=2)}")
    response = requests.post(RPC_URL, headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

    
    notify_payload ={
        "jsonrpc": "2.0",
        "method": "service.notify",
        "params": {
        "service": "4pc9typi",
        "msg": "No alerts detected",
        "tags": ["tags"]
    }
    }
    print(f"Payload (service.notify): {json.dumps(notify_payload, indent=2)}")
    notify_response = requests.post(RPC_URL, headers=headers, json=notify_payload)
    print(f"Notify Status: {notify_response.status_code}")
    print(f"Notify Response: {notify_response.text}")

    

if __name__ == "__main__":
    send_health_data()
