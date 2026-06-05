from __future__ import annotations

from pathlib import Path

import numpy as np

from .feature_utils import SampledFrame, cosine_similarity, simple_kmeans
from .video_loader import sample_video
from .yolo_optional import load_yolo, score_task_channels


def _top_positions(rows: list[dict], key: str, quota: int, positive: bool = True) -> list[int]:
    order = sorted(range(len(rows)), key=lambda i: rows[i].get(key, 0.0), reverse=True)
    out: list[int] = []
    for pos in order:
        if positive and rows[pos].get(key, 0.0) <= 0:
            continue
        out.append(pos)
        if len(out) >= quota:
            break
    return out


def _dedup_positions(candidates: list[int], samples: list[SampledFrame], budget: int, min_gap_frames: int, threshold: float) -> tuple[list[int], list[dict]]:
    selected: list[int] = []
    removed: list[dict] = []
    for pos in candidates:
        duplicate = None
        for kept_pos in selected:
            near_time = abs(samples[pos].frame_idx - samples[kept_pos].frame_idx) < min_gap_frames
            similar = cosine_similarity(samples[pos].feature, samples[kept_pos].feature)
            if (near_time and similar >= threshold) or similar >= 0.997:
                duplicate = {
                    "frame_idx": samples[pos].frame_idx,
                    "kept_frame_idx": samples[kept_pos].frame_idx,
                    "similarity": round(similar, 6),
                }
                break
        if duplicate:
            removed.append(duplicate)
        else:
            selected.append(pos)
        if len(selected) >= budget:
            break
    return selected, removed


def extract_keyframes(video_path: Path, config: dict) -> dict:
    info, samples = sample_video(
        video_path,
        sample_fps=float(config.get("sample_fps", 0.5)),
        max_samples=int(config.get("max_samples", 1200)),
        seek_sample=bool(config.get("seek_sample", True)),
    )
    budget = min(int(config.get("keyframe_budget", 44)), max(len(samples), 1))
    if not samples:
        raise RuntimeError(f"No frames sampled from video: {video_path}")

    weights = Path(str(config.get("yolo_weights", "weights/yolo26n.pt")))
    model, yolo_status = load_yolo(weights, bool(config.get("enable_yolo", True)))
    channel_rows = score_task_channels(samples, model, int(config.get("max_yolo_frames", 240)))
    features = np.stack([s.feature for s in samples], axis=0)

    kmeans_quota = max(1, round(budget * 0.50))
    uniform_quota = max(1, round(budget * 0.15))
    person_quota = max(0, round(budget * 0.10))
    object_quota = max(0, round(budget * 0.12))
    small_object_quota = max(0, round(budget * 0.08))
    proxy_quota = max(0, budget - kmeans_quota - uniform_quota - person_quota - object_quota - small_object_quota)

    kmeans_pos = simple_kmeans(features, kmeans_quota)
    uniform_pos = [int(i) for i in np.linspace(0, len(samples) - 1, uniform_quota, dtype=int)] if samples else []
    person_pos = _top_positions(channel_rows, "person_score", person_quota)
    object_pos = _top_positions(channel_rows, "object_score", object_quota)
    small_pos = _top_positions(channel_rows, "small_object_score", small_object_quota)
    proxy_order = sorted(range(len(channel_rows)), key=lambda i: channel_rows[i]["ocr_proxy_score"] + channel_rows[i]["clip_proxy_score"], reverse=True)[:proxy_quota]

    candidates: list[int] = []
    source_by_pos: dict[int, list[str]] = {}
    for source, group in [
        ("kmeans", kmeans_pos),
        ("uniform", uniform_pos),
        ("yolo_person", person_pos),
        ("yolo_object", object_pos),
        ("yolo_small_object", small_pos),
        ("ocr_clip_proxy", proxy_order),
    ]:
        for pos in group:
            if pos not in candidates:
                candidates.append(pos)
            source_by_pos.setdefault(pos, []).append(source)

    fill_order = sorted(range(len(samples)), key=lambda i: (samples[i].diff_score, i), reverse=True)
    for pos in fill_order:
        if pos not in candidates:
            candidates.append(pos)

    if bool(config.get("enable_dedup", True)):
        selected_pos, removed = _dedup_positions(
            candidates,
            samples,
            budget,
            int(config.get("dedup_min_gap_frames", 90)),
            float(config.get("dedup_threshold", 0.92)),
        )
        if len(selected_pos) < budget:
            for pos in fill_order:
                if pos not in selected_pos:
                    selected_pos.append(pos)
                if len(selected_pos) >= budget:
                    break
    else:
        selected_pos = candidates[:budget]
        removed = []

    selected_pos = sorted(selected_pos[:budget], key=lambda p: samples[p].frame_idx)
    keyframes = []
    for rank, pos in enumerate(selected_pos, start=1):
        row = channel_rows[pos]
        keyframes.append({
            "rank": rank,
            "frame_idx": samples[pos].frame_idx,
            "timestamp_sec": round(samples[pos].timestamp_sec, 3),
            "sources": source_by_pos.get(pos, ["fill"]),
            "diff_score": round(samples[pos].diff_score, 6),
            "scores": {k: row[k] for k in ["person_score", "object_score", "small_object_score", "ocr_proxy_score", "clip_proxy_score"]},
            "classes": row.get("classes", []),
        })

    return {
        "video_info": info.__dict__ | {"path": str(info.path)},
        "samples": samples,
        "keyframes": keyframes,
        "selected_positions": selected_pos,
        "channel_rows": channel_rows,
        "dedup_removed": removed,
        "yolo_status": yolo_status,
        "quotas": {
            "kmeans": kmeans_quota,
            "uniform": uniform_quota,
            "yolo_person": person_quota,
            "yolo_object": object_quota,
            "yolo_small_object": small_object_quota,
            "ocr_clip_proxy": proxy_quota,
        },
    }
