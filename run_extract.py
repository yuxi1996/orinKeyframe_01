from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from src.export_utils import ensure_output_dirs, save_keyframe_images, write_json
from src.html_report import write_keyframe_report
from src.keyframe_extractor import extract_keyframes


def load_config(path: Path) -> dict:
    try:
        import yaml  # type: ignore

        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        config: dict = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if ":" not in line or line.strip().startswith("#"):
                continue
            key, value = line.split(":", 1)
            value = value.strip()
            if value.lower() in {"true", "false"}:
                parsed = value.lower() == "true"
            else:
                try:
                    parsed = int(value) if value.isdigit() else float(value)
                except ValueError:
                    parsed = value
            config[key.strip()] = parsed
        return config


def serializable_result(result: dict) -> dict:
    clean = {k: v for k, v in result.items() if k not in {"samples"}}
    return clean


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract keyframes from one video file.")
    parser.add_argument("--video", required=True, help="Video file path, for example videos/test.mp4")
    parser.add_argument("--config", default="config/default.yaml")
    args = parser.parse_args()

    config = load_config(Path(args.config))
    output_dir = Path(str(config.get("output_dir", "outputs")))
    dirs = ensure_output_dirs(output_dir)
    video_path = Path(args.video)
    if not video_path.exists():
        raise SystemExit(f"Video not found: {video_path}")

    start = time.perf_counter()
    result = extract_keyframes(video_path, config)
    runtime = time.perf_counter() - start
    video_stem = video_path.stem

    keyframe_dir = dirs["keyframes"] / video_stem
    save_keyframe_images(keyframe_dir, result["samples"], result["selected_positions"], result["keyframes"])
    info = result["video_info"]
    metrics = {
        "video": video_path.name,
        "total_frames": info["total_frames"],
        "duration_sec": round(info["duration_sec"], 3),
        "processed_frames": len(result["samples"]),
        "keyframe_count": len(result["keyframes"]),
        "compression_ratio": round(info["total_frames"] / max(len(result["keyframes"]), 1), 3),
        "total_runtime_sec": round(runtime, 3),
        "yolo_status": result["yolo_status"],
    }
    result["metrics"] = metrics

    json_path = dirs["json"] / f"{video_stem}_keyframes.json"
    write_json(json_path, serializable_result(result))
    report_path = dirs["reports"] / f"{video_stem}_report.html"
    rel_image_dir = f"../keyframes/{video_stem}"
    write_keyframe_report(report_path, video_path.name, result["keyframes"], rel_image_dir, metrics)

    print(json.dumps({"json": str(json_path), "html": str(report_path), "keyframes": str(keyframe_dir), **metrics}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
