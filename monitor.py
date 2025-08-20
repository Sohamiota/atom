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
                env: str = "production",
                stype: str = "monitor",
                name: Optional[str] = None,
                project: Optional[str] = None,
                service: str = "4pc9typi",
                version: Optional[str] = None,
                auto_start: bool = False):

        self.atom = 1
        self.env = env
        self.stype = stype
        self.name = name if name else self._generate_worker_name()
        self.project = project if project else self._get_project_name()
        self.service = service
        self.version = version if version else self._get_version()
        self.user = getpass.getuser()
        self.running = False
        self.poll_interval = 10
        self.output_file = "health_data.json"
        self.capture_count = 0
        self.max_captures = None
        self.monitor_thread = None
        self.start_time = int(time.time() * 1000)
        self.auto_start = auto_start

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        if self.auto_start:
            self.start()

    def _generate_worker_name(self) -> str:
        return f"worker-{str(uuid.uuid4()).replace('-', '')[:10]}"

    def _get_project_name(self) -> str:
        try:
            result = subprocess.run(['git', 'remote', 'get-url', 'origin'],
                                    capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                url = result.stdout.strip()
                if '/' in url:
                    project = url.split('/')[-1].replace('.git', '')
                    return project[:6] if len(project) > 6 else project
        except:
            pass
        return "gvexwt"

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
        return "nogit" + str(int(time.time()))[:8]

    #def _get_primary_ip_address(self) -> str:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except:
            pass
        try:
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except:
            pass
        return "127.0.0.1"

    def _get_uptime(self):
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
                days = int(uptime_seconds // 86400)
                hours = int((uptime_seconds % 86400) // 3600)
                if days > 0:
                    return f"{days} days, {hours} hours"
                else:
                    return f"{hours} hours"
        except:
            try:
                boot_time = psutil.boot_time()
                uptime_seconds = time.time() - boot_time
                days = int(uptime_seconds // 86400)
                hours = int((uptime_seconds % 86400) // 3600)
                if days > 0:
                    return f"{days} days, {hours} hours"
                else:
                    return f"{hours} hours"
            except:
                try:
                    result = subprocess.run(['wmic', 'os', 'get', 'LastBootUpTime'],
                                            capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        return "system uptime available"
                except:
                    pass
                return "uptime unknown"

    def get_system_health(self) -> Dict[str, Any]:
        mem = psutil.virtual_memory()
        try:
            disk_io = psutil.disk_io_counters()
            if disk_io:
                diskrw = {
                    "reads": disk_io.read_count,
                    "writes": disk_io.write_count
                }
            else:
                diskrw = {"reads": 0, "writes": 0}
        except:
            diskrw = {"reads": 0, "writes": 0}

        try:
            if hasattr(os, 'getloadavg'):
                load_avg = os.getloadavg()
                load = {
                    "min1": f"{load_avg[0]:.2f}",
                    "min5": f"{load_avg[1]:.2f}",
                    "min15": f"{load_avg[2]:.2f}",
                    "uptime": self._get_uptime()
                }
            else:
                try:
                    cpu_count = psutil.cpu_count()
                    cpu_percent = psutil.cpu_percent(interval=0.1)
                    approx_load = (cpu_percent / 100.0) * cpu_count
                    load = {
                        "min1": f"{approx_load:.2f}",
                        "min5": f"{approx_load:.2f}",
                        "min15": f"{approx_load:.2f}",
                        "uptime": self._get_uptime()
                    }
                except:
                    load = {
                        "min1": "0.00",
                        "min5": "0.00",
                        "min15": "0.00",
                        "uptime": self._get_uptime()
                    }
        except:
            load = {
                "min1": "0.00",
                "min5": "0.00",
                "min15": "0.00",
                "uptime": "unknown"
            }

        try:
            cpu_times = psutil.cpu_times_percent(interval=1.0)
            cpu_stats = {
                "sy": round(cpu_times.system) if hasattr(cpu_times, 'system') else 0,
                "wa": round(cpu_times.iowait) if hasattr(cpu_times, 'iowait') else 0,
                "id": round(cpu_times.idle) if hasattr(cpu_times, 'idle') else 100,
                "us": round(cpu_times.user) if hasattr(cpu_times, 'user') else 0
            }
        except:
            try:
                cpu_percent = psutil.cpu_percent(interval=1.0)
                cpu_stats = {
                    "sy": round(cpu_percent * 0.3),
                    "wa": 0,
                    "id": round(100 - cpu_percent),
                    "us": round(cpu_percent * 0.7)
                }
            except:
                cpu_stats = {"sy": 0, "wa": 0, "id": 100, "us": 0}

        diskinfo = []
        try:
            partitions = psutil.disk_partitions()
            for partition in partitions:
                try:
                    disk_usage = psutil.disk_usage(partition.mountpoint)
                    if disk_usage.total > 0:
                        diskinfo.append({
                            "total": disk_usage.total // 1024,
                            "name": partition.mountpoint,
                            "used": round((disk_usage.used / disk_usage.total) * 100, 2),
                            "type": partition.fstype
                        })
                        break
                except (PermissionError, OSError):
                    continue
        except:
            pass

        if not diskinfo:
            try:
                if os.name == 'nt':
                    disk_usage = psutil.disk_usage('C:\\')
                    diskinfo = [{
                        "total": disk_usage.total // 1024,
                        "name": "C:\\",
                        "used": round((disk_usage.used / disk_usage.total) * 100, 2),
                        "type": "NTFS"
                    }]
                else:
                    disk_usage = psutil.disk_usage('/')
                    diskinfo = [{
                        "total": disk_usage.total // 1024,
                        "name": "/",
                        "used": round((disk_usage.used / disk_usage.total) * 100, 2),
                        "type": "ext4"
                    }]
            except:
                diskinfo = [{
                    "total": 0,
                    "name": "/unknown",
                    "used": 0.0,
                    "type": "unknown"
                }]

        try:
            net_io = psutil.net_io_counters()
            if net_io:
                network = {
                    "txbytes": net_io.bytes_sent // 1024,
                    "rxbytes": net_io.bytes_recv // 1024
                }
            else:
                network = {"txbytes": 0, "rxbytes": 0}
        except:
            network = {"txbytes": 0, "rxbytes": 0}

        current_commit = self._get_git_commit()

        payload = {
            "jsonrpc": "2.0",
            "method": "service.health",
            "params": {
                "atom": self.atom,
                "name": "AtomClient",
                "env": self.env,
                "project": "HealthMonitoring",
                "service": self.service,
                "stype": self.stype,
                "running": self.running,
                "info": {
                    "version": self.version,
                    "commit": current_commit
                },
                "logs": [
    {
        "ct": 1697744302000,
        "level": 2,
        "msg": "Sample log message"
    }
    ],
                "cpu": {
                    "diskrw": diskrw,
                    "core": psutil.cpu_count(),
                    "memory": {
                        "total": mem.total // (1024 * 1024),
                        "used": round(mem.percent)
                    },
                    "load": load,
                    "cpu": cpu_stats,
                    "diskinfo": diskinfo,
                    "network": network
                }
            }
        }
        return payload

    def check_anomalies(self, data: Dict[str, Any]):
        alerts = []
        try:
            mem_used = data["params"]["cpu"]["memory"]["used"]
            cpu_used = data["params"]["cpu"]["cpu"]["us"]
            disk_used = data["params"]["cpu"]["diskinfo"][0]["used"]

            if mem_used > 90:
                alerts.append(f"High memory usage ({mem_used}%)")
            if cpu_used > 85:
                alerts.append(f"High CPU usage ({cpu_used}%)")
            if disk_used > 95:
                alerts.append(f"High disk usage ({disk_used}%)")
        except Exception as e:
            self.logger.error(f"Anomaly check failed: {e}")

        if not alerts:
            alerts.append("No alerts detected")

        return alerts

    def _monitoring_loop(self):
        self.logger.info(f"Starting health monitoring with {self.poll_interval}s interval")
        while self.running:
            try:
                health_data = self.get_system_health()
                if health_data:
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Health Data Collected:")
                    print(json.dumps(health_data, indent=2))
                    print("-" * 80)

                    alerts = self.check_anomalies(health_data)
                    self.logger.warning(f"Alerts detected: {alerts}")

                    self._save_health_data(health_data)
                    self.capture_count += 1
                    self.logger.info(f"Health data collected (capture {self.capture_count})")

                    if self.max_captures and self.capture_count >= self.max_captures:
                        self.logger.info(f"Reached max captures ({self.max_captures}). Stopping monitor.")
                        self.running = False
                        break

                time.sleep(self.poll_interval)
            except KeyboardInterrupt:
                self.logger.info("Monitoring interrupted by user")
                self.running = False
                break
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

        self.logger.info(f"Starting health monitor - interval: {interval}s, output: {output_file}")
        if max_captures:
            self.logger.info(f"Will stop after {max_captures} captures")

        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()

        return self

    def stop(self):
        if not self.running:
            self.logger.info("Monitor is not running")
            return False

        self.logger.info("Stopping health monitor...")
        self.running = False

        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)

        self.logger.info(f"Health monitor stopped. Total captures: {self.capture_count}")
        return True

    def wait_for_completion(self):
        if self.monitor_thread and self.monitor_thread.is_alive():
            try:
                self.monitor_thread.join()
            except KeyboardInterrupt:
                self.logger.info("Interrupted while waiting for completion")
                self.stop()

    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self.running,
            "captures_collected": self.capture_count,
            "max_captures": self.max_captures,
            "poll_interval": self.poll_interval,
            "output_file": self.output_file,
            "thread_alive": self.monitor_thread.is_alive() if self.monitor_thread else False
        }

    def get_health_data(self, interval: int = None, captures: int = None) -> Any:
        if interval and captures:
            self.start(interval=interval, max_captures=captures)
            while self.is_running():
                time.sleep(1)
            if os.path.exists(self.output_file):
                with open(self.output_file, 'r') as f:
                    return json.load(f)
            return {}
        else:
            return self.get_system_health()

    def is_running(self) -> bool:
        return self.running


if __name__ == "__main__":
    import sys

    interval = 10
    max_captures = None
    auto_start = True

    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
        except ValueError:
            print("Invalid interval. Using default 10 seconds.")

    if len(sys.argv) > 2:
        try:
            max_captures = int(sys.argv[2])
        except ValueError:
            print("Invalid max_captures. Running indefinitely.")

    print(f"Health Monitor Starting...")
    print(f"Interval: {interval} seconds")
    print(f"Max captures: {max_captures if max_captures else 'Unlimited'}")
    print("Press Ctrl+C to stop\n")

    monitor = HealthMonitor()

    try:
        monitor.start(interval=interval, max_captures=max_captures)
        while monitor.is_running():
            time.sleep(5)
        print("\nMonitoring completed!")
    except KeyboardInterrupt:
        print("\nStopping monitor...")
        monitor.stop()
        print("Monitor stopped.")
