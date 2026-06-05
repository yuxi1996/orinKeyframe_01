from __future__ import annotations

import argparse
import json
import platform
import shutil
import sys
import time
from pathlib import Path

import cv2

from run_extract import load_config, serializable_result
from src.export_utils import append_csv, ensure_output_dirs, save_keyframe_images, write_json
from src.html_report import write_benchmark_report, write_keyframe_report
from src.keyframe_extractor import extract_keyframes
from src.metrics_monitor import MetricsMonitor
from src.video_loader import list_videos


def dependency_versions() -> dict:
    cuda = "N/A"
    tensorrt = "N/A"
    try:
        import torch  # type: ignore

        cuda = getattr(torch.version, "cuda", None) or "N/A"
    except Exception:
        pass
    try:
        import tensorrt  # type: ignore

        tensorrt = getattr(tensorrt, "__version__", "available")
    except Exception:
        pass
    return {
        "platform": platform.platform(),
        "opencv_version": cv2.__version__,
        "cuda_version_if_available": cuda,
        "tensorrt_version_if_available": tensorrt,
        "tegrastats_available": bool(shutil.which("tegrastats")),
    }


def order_videos(videos: list[Path], order_file: str | None) -> list[Path]:
    if not order_file:
        return videos
    path = Path(order_file)
    if not path.exists():
        return videos
    ordered_ids = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    rank = {uid: i for i, uid in enumerate(ordered_ids)}
    return sorted(videos, key=lambda p: (rank.get(p.stem, 10**9), p.name.lower()))


def benchmark_one(video_path: Path, config: dict, dirs: dict[str, Path]) -> dict:
    monitor = MetricsMonitor(interval_sec=0.5, tegrastats_log=dirs["logs"] / "tegrastats.log")
    monitor.start()
    start = time.perf_counter()
    result = extract_keyframes(video_path, config)
    runtime = time.perf_counter() - start
    monitor_metrics = monitor.stop()

    info = result["video_info"]
    video_stem = video_path.stem
    keyframe_dir = dirs["keyframes"] / video_stem
    save_keyframe_images(keyframe_dir, result["samples"], result["selected_positions"], result["keyframes"])

    processed_frames = len(result["samples"])
    keyframe_count = len(result["keyframes"])
    row = {
        "video": video_path.name,
        "total_frames": info["total_frames"],
        "duration_sec": round(info["duration_sec"], 3),
        "processed_frames": processed_frames,
        "sample_fps": config.get("sample_fps", 0.5),
        "keyframe_count": keyframe_count,
        "compression_ratio": round(info["total_frames"] / max(keyframe_count, 1), 3),
        "total_runtime_sec": round(runtime, 3),
        "processing_fps_original_frames": round(info["total_frames"] / max(runtime, 1e-9), 3),
        "processing_fps_sampled_frames": round(processed_frames / max(runtime, 1e-9), 3),
        "avg_time_per_original_frame": round(runtime / max(info["total_frames"], 1), 6),
        "avg_time_per_processed_frame": round(runtime / max(processed_frames, 1), 6),
        **monitor_metrics,
        **dependency_versions(),
        "yolo_status": result["yolo_status"],
    }
    result["metrics"] = row
    write_json(dirs["json"] / f"{video_stem}_keyframes.json", serializable_result(result))
    write_keyframe_report(dirs["reports"] / f"{video_stem}_report.html", video_path.name, result["keyframes"], f"../keyframes/{video_stem}", row)
    return row


def write_create_project_summary(path: Path, rows: list[dict], videos_found: int) -> None:
    files = sorted(
        str(p).replace("\\", "/")
        for p in Path(".").rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    )
    status = "OK" if videos_found else "No mp4 videos found; benchmark generated placeholder outputs."
    text = "\n".join([
        "# orinKeyframe_01 create project summary",
        "",
        "## Created files",
        *files,
        "",
        "## Current Windows verification result",
        status,
        f"Python: {sys.version.split()[0]}",
        f"Rows: {len(rows)}",
        "",
        "## Orin run commands",
        "python3 scripts/check_env.py",
        "python3 run_benchmark.py --video_dir videos",
        "bash scripts/monitor_tegrastats.sh",
        "",
        "## Manual video input",
        "Put .mp4 files into orinKeyframe_01/videos, or use the integrated X-Lebench path:",
        'python3 run_benchmark.py --video_dir "datasets/X-Lebench数据集（部分）/Ego4D/v2/full_scale" --config config/xlebench.yaml',
        "",
        "## Manual YOLO weights input",
        "Optional: put weights/yolo26n.pt under this project. If missing, the code falls back to non-YOLO extraction.",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark portable keyframe extraction on video files.")
    parser.add_argument("--video", default=None)
    parser.add_argument("--video_dir", default=None)
    parser.add_argument("--config", default="config/default.yaml")
    args = parser.parse_args()

    config = load_config(Path(args.config))
    output_dir = Path(str(config.get("output_dir", "outputs")))
    dirs = ensure_output_dirs(output_dir)

    if args.video:
        videos = [Path(args.video)]
    else:
        video_dir = Path(args.video_dir or str(config.get("video_dir", "videos")))
        videos = list_videos(video_dir)
    videos = order_videos(videos, config.get("order_file"))

    if not videos:
        message = "Please put .mp4 files into orinKeyframe_01/videos and rerun benchmark."
        print(message)
        write_json(dirs["json"] / "benchmark_summary.json", {"status": "no_videos", "message": message, "videos": []})
        write_benchmark_report(dirs["reports"] / "benchmark_report.html", [])
        write_create_project_summary(dirs["logs"] / "create_project_summary.txt", [], 0)
        return

    rows: list[dict] = []
    for video in videos:
        if not video.exists():
            print(f"Skip missing video: {video}")
            continue
        try:
            row = benchmark_one(video, config, dirs)
            rows.append(row)
            print(json.dumps(row, ensure_ascii=False))
        except Exception as exc:
            rows.append({"video": str(video), "error": str(exc), **dependency_versions()})

    append_csv(dirs["logs"] / "benchmark.csv", rows)
    write_json(dirs["json"] / "benchmark_summary.json", {"videos": rows, "count": len(rows)})
    write_benchmark_report(dirs["reports"] / "benchmark_report.html", rows)
    write_create_project_summary(dirs["logs"] / "create_project_summary.txt", rows, len(videos))
    print(f"Benchmark outputs: {output_dir}")


if __name__ == "__main__":
    main()
