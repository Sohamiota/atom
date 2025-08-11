import json
import os
import sys
import time

import requests

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from monitor import HealthMonitor

monitor = HealthMonitor()

API_URL = "http://10.83.51.106:5000/health"

print("Starting real-time health monitoring. Press Ctrl+C to stop.")
try:
    while True:
        health_data = monitor.get_health_data()
        try:
            response = requests.post(
                API_URL,
                headers={"Content-Type": "application/json"},
                data=json.dumps(health_data)
            )

            if response.status_code == 200:
                print("Health log sent successfully.")
            else:
                print(f"Failed: {response.status_code} - {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")

        time.sleep(10)
except KeyboardInterrupt:
    print("\nReal-time monitoring stopped by user.")
