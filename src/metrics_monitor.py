from __future__ import annotations

import shutil
import threading
import time
from pathlib import Path

from .tegrastats_parser import parse_tegrastats_file


class MetricsMonitor:
    def __init__(self, interval_sec: float = 0.5, tegrastats_log: Path | None = None) -> None:
        self.interval_sec = interval_sec
        self.tegrastats_log = tegrastats_log
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.cpu: list[float] = []
        self.mem_mb: list[float] = []
        self.mem_percent: list[float] = []

    def start(self) -> None:
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> dict:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)
        return self.summary()

    def _run(self) -> None:
        try:
            import psutil  # type: ignore
        except Exception:
            return
        proc = psutil.Process()
        while not self._stop.is_set():
            self.cpu.append(float(psutil.cpu_percent(interval=None)))
            mem = proc.memory_info().rss / 1024**2
            self.mem_mb.append(float(mem))
            self.mem_percent.append(float(psutil.virtual_memory().percent))
            time.sleep(self.interval_sec)

    def summary(self) -> dict:
        def avg(values: list[float]):
            return round(sum(values) / len(values), 3) if values else "N/A"

        gpu = {
            "gpu_avg_percent": "N/A",
            "gpu_max_percent": "N/A",
            "power_avg_mw": "N/A",
            "power_max_mw": "N/A",
            "temperature_avg_c": "N/A",
            "temperature_max_c": "N/A",
            "tegrastats_available": bool(shutil.which("tegrastats")),
        }
        if self.tegrastats_log and self.tegrastats_log.exists():
            gpu.update(parse_tegrastats_file(self.tegrastats_log))
            gpu["tegrastats_available"] = True
        return {
            "cpu_avg_percent": avg(self.cpu),
            "cpu_max_percent": max(self.cpu) if self.cpu else "N/A",
            "memory_avg_mb": avg(self.mem_mb),
            "memory_max_mb": max(self.mem_mb) if self.mem_mb else "N/A",
            "memory_avg_percent": avg(self.mem_percent),
            "memory_max_percent": max(self.mem_percent) if self.mem_percent else "N/A",
            **gpu,
        }
