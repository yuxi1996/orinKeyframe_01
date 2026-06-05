# Windows Verification

Run from the project root:

```bat
cd orinKeyframe_01
python scripts/check_env.py
python run_benchmark.py --video_dir videos
```

Or use:

```bat
scripts\run_windows_verify.bat
```

Expected Windows behavior:

- CPU and memory metrics are collected with `psutil`.
- `tegrastats` is normally unavailable, so GPU, power, and temperature fields are `N/A`.
- Jetson-specific fields such as L4T version are `N/A`.
- If no videos are present, benchmark output is still generated with the message:

```text
Please put .mp4 files into orinKeyframe_01/videos and rerun benchmark.
```

Generated verification files:

```text
outputs/json/benchmark_summary.json
outputs/reports/benchmark_report.html
outputs/logs/create_project_summary.txt
```
