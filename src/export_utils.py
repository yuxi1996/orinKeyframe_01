from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

import cv2


def ensure_output_dirs(output_dir: Path) -> dict[str, Path]:
    dirs = {
        "keyframes": output_dir / "keyframes",
        "json": output_dir / "json",
        "reports": output_dir / "reports",
        "logs": output_dir / "logs",
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    return dirs


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def save_keyframe_images(out_dir: Path, samples: list, selected_positions: list[int], keyframes: list[dict]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for pos, meta in zip(selected_positions, keyframes):
        frame = samples[pos].frame_bgr
        name = f"{meta['rank']:04d}_frame_{meta['frame_idx']:08d}.jpg"
        cv2.imwrite(str(out_dir / name), frame)
        meta["image"] = name


def append_csv(path: Path, rows: Iterable[dict]) -> None:
    rows = list(rows)
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerows(rows)
