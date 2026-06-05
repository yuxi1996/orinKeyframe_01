from __future__ import annotations

import re
from pathlib import Path


def _numbers(pattern: str, text: str) -> list[float]:
    return [float(x) for x in re.findall(pattern, text)]


def parse_tegrastats_text(text: str) -> dict:
    gpu = _numbers(r"GR3D_FREQ\s+(\d+(?:\.\d+)?)%", text)
    ram = _numbers(r"RAM\s+(\d+(?:\.\d+)?)/", text)
    temps = _numbers(r"@\s*(\d+(?:\.\d+)?)C", text)
    powers = _numbers(r"(?:VDD_GPU_SOC|VDD_CPU_CV|VIN_SYS_5V0)\s+(\d+(?:\.\d+)?)(?:mW)?/", text)
    return {
        "gpu_avg_percent": round(sum(gpu) / len(gpu), 3) if gpu else "N/A",
        "gpu_max_percent": max(gpu) if gpu else "N/A",
        "ram_avg_mb": round(sum(ram) / len(ram), 3) if ram else "N/A",
        "ram_max_mb": max(ram) if ram else "N/A",
        "power_avg_mw": round(sum(powers) / len(powers), 3) if powers else "N/A",
        "power_max_mw": max(powers) if powers else "N/A",
        "temperature_avg_c": round(sum(temps) / len(temps), 3) if temps else "N/A",
        "temperature_max_c": max(temps) if temps else "N/A",
    }


def parse_tegrastats_file(path: Path) -> dict:
    if not path.exists():
        return parse_tegrastats_text("")
    return parse_tegrastats_text(path.read_text(errors="ignore"))
