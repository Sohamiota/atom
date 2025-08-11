import getpass
import json
import logging
import os
import socket
import subprocess
import threading
import time
import uuid
from typing import Any, Dict, Optional

import psutil


class HealthMonitor:
    def __init__(self,
                worker_id: Optional[str] = None,
                worker_name: Optional[str] = None,
                project: Optional[str] = None,
                user: Optional[str] = None,
                version: Optional[str] = None,
                env: str = "prod",
                stype: str = "worker"):

        self.worker_id = worker_id if worker_id else self._generate_worker_id()
        self.worker_name = worker_name if worker_name else self._generate_worker_name()
        self.project = project if project else self._get_project_name()
        self.user = user if user else getpass.getuser()
        self.version = version if version else self._get_version()
        self.env = env
        self.stype = stype
        self.start_time = int(time.time() * 1000)
        self.stop_time = 0
        self.running = False
        self.monitor_thread = None
        self.poll_interval = 10
        self.output_file = "health_data.json"
        self.capture_count = 0
        self.max_captures = None

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _generate_worker_id(self) -> str:
        return str(uuid.uuid4())[:8]

    def _generate_worker_name(self) -> str:
        hostname = socket.gethostname()
        return f"worker-{hostname}-{str(uuid.uuid4())[:8]}"

    def _get_project_name(self) -> str:
        try:
            result = subprocess.run(['git', 'remote', 'get-url', 'origin'],
                                    capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                url = result.stdout.strip()
                if '/' in url:
                    return url.split('/')[-1].replace('.git', '')
        except:
            pass
        return os.path.basename(os.getcwd())

    def _get_version(self) -> str:
        try:
            result = subprocess.run(['git', 'describe', '--tags', '--abbrev=0'],
                                    capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
            result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'],
                                    capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return f"git-{result.stdout.strip()}"
        except:
            pass
        return "v1.0.0"

    def _get_git_commit(self) -> str:
        try:
            result = subprocess.run(['git', 'rev-parse', 'HEAD'],
                                    capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return "unknown"

    def _get_primary_ip_address(self) -> dict:
        """Get only one primary IP address"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                return {
                    "interface": "primary",
                    "ip": ip,
                    "netmask": None,
                    "type": "IPv4"
                }
        except:
            pass
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            return {
                "interface": "primary",
                "ip": ip,
                "netmask": None,
                "type": "IPv4"
            }
        except:
            pass
        return {
            "interface": "localhost",
            "ip": "127.0.0.1",
            "netmask": "255.0.0.0",
            "type": "IPv4"
        }

    def get_system_health(self) -> Dict[str, Any]:
        try:
            current_time = int(time.time() * 1000)
            cpu_times = psutil.cpu_times_percent(interval=1)
            memory = psutil.virtual_memory()
            disk_usage = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            network_io = psutil.net_io_counters()

            try:
                if hasattr(os, 'getloadavg'):
                    load_avg = os.getloadavg()
                    load_info = {
                        "min5": f"{load_avg[1]:.2f}",
                        "min15": f"{load_avg[2]:.2f}",
                        "min1": "",
                        "uptime": self._get_uptime()
                    }
                else:
                    load_info = {
                        "min5": "0.00",
                        "min15": "0.00",
                        "min1": "",
                        "uptime": self._get_uptime()
                    }
            except:
                load_info = {
                    "min5": "0.00",
                    "min15": "0.00",
                    "min1": "",
                    "uptime": self._get_uptime()
                }

            primary_ip = self._get_primary_ip_address()

            health_data = {
                "id": self.worker_id,
                "name": self.worker_name,
                "stype": self.stype,
                "project": self.project,
                "env": self.env,
                "ct": current_time,
                "mt": current_time,
                "alivets": current_time,
                "status": 1 if self.running else 0,
                "running": self.running,
                "starttime": self.start_time,
                "stoptime": self.stop_time,
                "version": self.version,
                "user": self.user,
                "deploy": self.start_time,
                "commit": self._get_git_commit(),
                "ip": primary_ip,
                "hosts": None,
                "ssl": "",
                "poll": self.poll_interval * 1000,
                "health": {
                    "diskrw": {
                        "reads": int(disk_io.read_count if disk_io else 0),
                        "writes": int(disk_io.write_count if disk_io else 0)
                    },
                    "core": psutil.cpu_count(),
                    "memory": {
                        "total": int(round(memory.total / (1024**2))),
                        "used": int(round(memory.percent))
                    },
                    "load": load_info,
                    "cpu": {
                        "sy": int(round(cpu_times.system if hasattr(cpu_times, 'system') else 0)),
                        "wa": int(round(cpu_times.iowait if hasattr(cpu_times, 'iowait') else 0)),
                        "id": int(round(cpu_times.idle if hasattr(cpu_times, 'idle') else 0)),
                        "us": int(round(cpu_times.user if hasattr(cpu_times, 'user') else 0))
                    },
                    "diskinfo": [{
                        "total": int(disk_usage.total // 1024),
                        "name": "/conf",
                        "used": round(disk_usage.percent, 2),
                        "type": "ext4"
                    }],
                    "network": {
                        "txbytes": int(network_io.bytes_sent if network_io else 0),
                        "rxbytes": int(network_io.bytes_recv if network_io else 0)
                    }
                }
            }
            return health_data
        except Exception as e:
            self.logger.error(f"Error collecting health metrics: {e}")
            return {}

    def _get_uptime(self) -> str:
        try:
            uptime_seconds = time.time() - psutil.boot_time()
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            if days > 0:
                return f"{days} days"
            elif hours > 0:
                return f"{hours} hours"
            else:
                return "< 1 hour"
        except:
            return "unknown"

    def _monitoring_loop(self):
        self.logger.info(f"Starting health monitoring with {self.poll_interval}s interval")
        if self.max_captures:
            self.logger.info(f"Will automatically stop after {self.max_captures} captures")

        while self.running:
            try:
                health_data = self.get_system_health()
                if health_data:
                    self._save_health_data(health_data)
                    self.capture_count += 1
                    self.logger.info(f"Health data collected (capture {self.capture_count})")
                    if self.max_captures and self.capture_count >= self.max_captures:
                        self.running = False
                        break
                time.sleep(self.poll_interval)
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)

    def _save_health_data(self, health_data: Dict[str, Any]):
        try:
            existing_data = []
            if os.path.exists(self.output_file):
                try:
                    with open(self.output_file, 'r') as f:
                        content = f.read().strip()
                        if content:
                            existing_data = json.loads(content)
                            if not isinstance(existing_data, list):
                                existing_data = [existing_data]
                except:
                    existing_data = []
            existing_data.append(health_data)
            if len(existing_data) > 1000:
                existing_data = existing_data[-1000:]
            with open(self.output_file, 'w') as f:
                json.dump(existing_data, f, indent=2, separators=(',', ': '))
        except Exception as e:
            self.logger.error(f"Error saving health data: {e}")

    def start(self, interval: int = 10, output_file: str = "health_data.json", max_captures: Optional[int] = None):
        if self.running:
            self.logger.warning("Monitor is already running!")
            return
        self.poll_interval = interval
        self.output_file = output_file
        self.max_captures = max_captures
        self.capture_count = 0
        self.running = True
        self.start_time = int(time.time() * 1000)
        self.stop_time = 0
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()

    def stop(self):
        if not self.running:
            return False
        self.running = False
        self.stop_time = int(time.time() * 1000)
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        return True

    def get_health_data(self, interval: int = None, captures: int = None) -> Dict[str, Any]:
        """
        Fetch health data.
        If interval & captures are provided, it will run monitoring loop and collect multiple snapshots.
        """
        if interval and captures:
            self.start(interval=interval, max_captures=captures)
            while self.is_running():
                time.sleep(1)
            # Load final data
            if os.path.exists(self.output_file):
                with open(self.output_file, 'r') as f:
                    return json.load(f)
            return {}
        else:
            return self.get_system_health()

    def get_current_status(self) -> Dict[str, Any]:
        return self.get_system_health()

    def is_running(self) -> bool:
        return self.running


if __name__ == "__main__":
    monitor = HealthMonitor()
    try:
        # Example: Collect 2 captures every 5 seconds
        data = monitor.get_health_data(interval=5, captures=2)
        print(json.dumps(data, indent=2))
    except KeyboardInterrupt:
        monitor.stop()
