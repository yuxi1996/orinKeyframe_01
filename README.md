# orinKeyframe_01

Portable video-file keyframe performance benchmark for NVIDIA Jetson AGX Orin Developer Kit. This project only tests video files. It does not use cameras.

## Known Orin Environment

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
| tegrastats | `/usr/bin/tegrastats` |

Important constraints:

- Use Jetson Linux R36.x / L4T R36.4.7 wording.
- This benchmark does not require cameras.
- The code does not depend on OpenCV CUDA.
- On Orin, GPU utilization is parsed from `tegrastats` `GR3D_FREQ`.
- On Windows, GPU and power fields may be `N/A`.
- YOLO is optional. If `weights/yolo26n.pt` is missing, the project falls back to non-YOLO keyframe extraction.

## Windows Verification

```bat
cd orinKeyframe_01
scripts\run_windows_verify.bat
```

Manual commands:

```bat
cd orinKeyframe_01
python scripts/check_env.py
python run_benchmark.py --video_dir videos
```

If `videos` has no `.mp4` files, the benchmark prints:

```text
Please put .mp4 files into orinKeyframe_01/videos and rerun benchmark.
```

## Orin Deployment

Copy the whole `orinKeyframe_01` folder to Orin, then run:

```bash
cd orinKeyframe_01
python3 -m pip install -r requirements.txt
python3 scripts/check_env.py
python3 run_benchmark.py --video_dir videos
```

Optional tegrastats monitor:

```bash
bash scripts/monitor_tegrastats.sh
```

In another terminal:

```bash
python3 run_benchmark.py --video_dir videos
```

## Video Placement

Put input `.mp4` files in:

```text
videos/
```

This project includes the partial X-Lebench annotation and download/order scripts under:

```text
datasets/X-Lebench数据集（部分）/
```

Large `.mp4` videos are not bundled. Re-download them on Orin with the Ego4D CLI.

Download X-Lebench related Ego4D videos on Orin:

```bash
python3 scripts/download_xlebench_ego4d.py
```

Dry run to inspect the video IDs and command:

```bash
python3 scripts/download_xlebench_ego4d.py --dry_run
```

Prepare the downloaded videos in user order:

```bash
python3 scripts/prepare_xlebench_order.py --mode manifest
```

If you want ordered symlinks:

```bash
python3 scripts/prepare_xlebench_order.py --mode symlink
```

Single video:

```bash
python run_extract.py --video videos/test.mp4 --config config/default.yaml
```

Batch benchmark:

```bash
python run_benchmark.py --video_dir videos
```

X-Lebench dataset benchmark:

```bash
python run_benchmark.py --video_dir "datasets/X-Lebench数据集（部分）/Ego4D/v2/full_scale" --config config/xlebench.yaml
```

Small X-Lebench smoke test:

```bash
python run_extract.py --video "datasets/X-Lebench数据集（部分）/Ego4D/v2/full_scale/9061bd1f-52ee-4aee-bbff-93c186cca302.mp4" --config config/xlebench.yaml
```

## Outputs

Single-video extraction writes:

```text
outputs/keyframes/<video_name>/
outputs/json/<video_name>_keyframes.json
outputs/reports/<video_name>_report.html
```

Benchmark writes:

```text
outputs/logs/benchmark.csv
outputs/json/benchmark_summary.json
outputs/reports/benchmark_report.html
outputs/logs/create_project_summary.txt
```

Dataset integration notes:

```text
docs/xlebench_dataset.md
config/xlebench.yaml
```

## Algorithm

Default flow:

```text
video file input
-> sample by sample_fps
-> Uniform candidates
-> KMeans candidates
-> optional YOLO person/object/small-object scores
-> optional OCR/CLIP proxy scores
-> multi-channel quota fusion
-> dedup
-> output keyframe images, JSON, HTML, benchmark CSV
```

Default parameters live in `config/default.yaml`.

## Common Issues

- `videos` has no `.mp4`: put videos into `videos/` and rerun.
- `weights/yolo26n.pt` is missing: YOLO is disabled automatically and logs `YOLO weights not found, fallback to non-YOLO keyframe extraction.`
- OpenCV CUDA devices is `0`: expected for the known Orin environment; this code uses CPU OpenCV.
- Windows has no `tegrastats`: GPU, power, and temperature fields are `N/A`.
- Orin has no camera devices: expected; this project only benchmarks video files.

## Current Limits

- No camera input.
- No dependency on OpenCV CUDA.
- YOLO is optional.
- GPU utilization is based on `tegrastats` when available.
