import logging
import subprocess
import threading
import time
from typing import Dict, List


class LogPayload:
    def __init__(self, timestamp: int, level: int, message: str):
        self.timestamp = timestamp
        self.level = level
        self.message = message

    def to_dict(self) -> Dict[str, object]:
        return {"ct": self.timestamp, "level": self.level, "msg": self.message}

class LogCollector(logging.Handler):
    def __init__(self):
        super().__init__()
        self.log_arr: List[LogPayload] = []
        self.log_mutex = threading.Lock()

    def emit(self, record: logging.LogRecord):
        if record.levelno == logging.DEBUG:
            return
        entry = LogPayload(
            timestamp=int(record.created * 1000),
            level=record.levelno,
            message=record.getMessage()
        )
        with self.log_mutex:
            self.log_arr.append(entry)

    def get_logs(self) -> List[Dict[str, object]]:
        with self.log_mutex:
            arr, self.log_arr = self.log_arr, []
        return [log.to_dict() for log in arr]

collector = LogCollector()
logger = logging.getLogger("MonitorLogger")
logger.setLevel(logging.INFO)
logger.addHandler(collector)

logger.info("System monitor started.")
logger.warning("CPU usage is high.")

def read_system_logs(cmd: str = "journalctl -n 5"):
    try:
        output = subprocess.check_output(cmd, shell=True, text=True)
        for line in output.strip().splitlines():
            logger.info(f"[SYSLOG] {line}")
    except Exception as e:
        logger.error(f"Failed to read system logs: {e}")

def flush_logs() -> List[Dict[str, object]]:
    logs = collector.get_logs()
    if logs:
        print("Sending logs:", logs)
    return logs
