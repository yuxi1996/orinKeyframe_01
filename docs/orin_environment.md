# Orin Environment

| Item | Value |
|---|---|
| Device | NVIDIA Jetson AGX Orin Developer Kit |
| OS | Ubuntu 22.04.5 LTS |
| Kernel | Linux 5.15.148-tegra aarch64 |
| Jetson Linux / L4T | R36.4.7 |
| Architecture | aarch64 |
| CPU | 12-core Cortex-A78AE |
| Memory | 61 GiB |
| Swap | 20 GiB |
| /home disk | /dev/nvme0n1p1, about 916G |
| Power mode | MAXN |
| CUDA | 12.6 |
| TensorRT | 10.3.0.30 |
| OpenCV | 4.13.0 |
| OpenCV CUDA devices | 0 |
| OpenCV GStreamer | True |
| Camera devices | current `/dev/video*` absent |
| tegrastats path | `/usr/bin/tegrastats` |

The benchmark uses video files only. Camera devices are reported by `scripts/check_env.py` but are not required.

OpenCV CUDA is not required because the known environment reports zero OpenCV CUDA devices. GPU usage on Orin is parsed from `tegrastats` `GR3D_FREQ`.
