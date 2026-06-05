# X-Lebench Download And Order Setup

The portable project keeps X-Lebench metadata and scripts only. Large `.mp4` videos are intentionally not bundled because they should be re-downloaded on Orin.

```text
datasets/X-Lebench数据集（部分）/
```

Included:

| Type | Count | Notes |
|---|---:|---|
| annotation JSON | 1 | `simulation_0120dffb_0d0b4c6b_annotation.json` |
| order file | 1 | `datasets/video_order_user.png_list.txt` |
| download script | 1 | `scripts/download_xlebench_ego4d.py` |
| order script | 1 | `scripts/prepare_xlebench_order.py` |

Excluded files:

- complete `.mp4` videos
- incomplete temporary downloads ending with `.mp4.*`
- Ego4D credential/config files

Install Ego4D CLI on Orin:

```bash
python3 -m pip install ego4d
```

Run a dry run first:

```bash
python3 scripts/download_xlebench_ego4d.py --dry_run
```

Download videos:

```bash
python3 scripts/download_xlebench_ego4d.py
```

If your Ego4D access requires explicit AWS files, pass them without storing them in this project:

```bash
python3 scripts/download_xlebench_ego4d.py \
  --aws_config /path/to/config \
  --aws_credentials /path/to/credentials
```

After download, the expected video directory is:

```text
datasets/X-Lebench数据集（部分）/Ego4D/v2/full_scale
```

Generate an ordered manifest:

```bash
python3 scripts/prepare_xlebench_order.py --mode manifest
```

Generate ordered symlinks when desired:

```bash
python3 scripts/prepare_xlebench_order.py --mode symlink
```

Run a full dataset benchmark after download:

```bash
python run_benchmark.py --video_dir "datasets/X-Lebench数据集（部分）/Ego4D/v2/full_scale" --config config/xlebench.yaml
```

Run one video:

```bash
python run_extract.py --video "datasets/X-Lebench数据集（部分）/Ego4D/v2/full_scale/9061bd1f-52ee-4aee-bbff-93c186cca302.mp4" --config config/xlebench.yaml
```

YOLO remains optional. If `weights/yolo26n.pt` is absent, the benchmark falls back to non-YOLO keyframe extraction.
