from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True, timeout=5).strip()
    except Exception as exc:
        return f"N/A ({exc})"


def opencv_info() -> dict:
    try:
        import cv2

        build = cv2.getBuildInformation()
        return {
            "OpenCV version": cv2.__version__,
            "OpenCV CUDA devices": cv2.cuda.getCudaEnabledDeviceCount() if hasattr(cv2, "cuda") else 0,
            "OpenCV GStreamer": "GStreamer:                   YES" in build or "GStreamer: YES" in build,
        }
    except Exception as exc:
        return {"OpenCV": f"N/A ({exc})"}


def mem_info() -> str:
    try:
        import psutil

        vm = psutil.virtual_memory()
        return f"{vm.total / 1024**3:.2f} GiB"
    except Exception:
        return "N/A"


def disk_info() -> str:
    usage = shutil.disk_usage(".")
    return f"total={usage.total / 1024**3:.2f} GiB free={usage.free / 1024**3:.2f} GiB"


def jetson_release() -> str:
    p = Path("/etc/nv_tegra_release")
    return p.read_text(errors="ignore").strip() if p.exists() else "N/A"


def device_model() -> str:
    p = Path("/proc/device-tree/model")
    return p.read_text(errors="ignore").replace("\x00", "").strip() if p.exists() else platform.node()


def main() -> None:
    data = {
        "Device model": device_model(),
        "L4T version": jetson_release(),
        "Ubuntu version": run(["lsb_release", "-ds"]) if shutil.which("lsb_release") else "N/A",
        "Python version": sys.version.split()[0],
        **opencv_info(),
        "CUDA version": run(["nvcc", "--version"]) if shutil.which("nvcc") else "N/A",
        "TensorRT version": run(["python3", "-c", "import tensorrt as trt; print(trt.__version__)"]),
        "CPU cores": os.cpu_count(),
        "Memory": mem_info(),
        "Disk": disk_info(),
        "tegrastats available": bool(shutil.which("tegrastats")),
        "/dev/video*": sorted(str(p) for p in Path("/dev").glob("video*")) if Path("/dev").exists() else [],
        "Platform": platform.platform(),
        "Machine": platform.machine(),
    }
    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
