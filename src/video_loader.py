from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2

from .feature_utils import SampledFrame, frame_feature

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".m4v"}


@dataclass
class VideoInfo:
    path: Path
    name: str
    stem: str
    total_frames: int
    fps: float
    duration_sec: float
    width: int
    height: int


def list_videos(video_dir: Path) -> list[Path]:
    if not video_dir.exists():
        return []
    return sorted(p for p in video_dir.rglob("*") if p.suffix.lower() in VIDEO_EXTS)


def get_video_info(path: Path) -> VideoInfo | None:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return None
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    cap.release()
    duration = total_frames / fps if fps > 0 else 0.0
    return VideoInfo(path, path.name, path.stem, total_frames, fps, duration, width, height)


def sample_video(path: Path, sample_fps: float, max_samples: int, seek_sample: bool = True) -> tuple[VideoInfo, list[SampledFrame]]:
    info = get_video_info(path)
    if info is None:
        raise RuntimeError(f"Cannot open video: {path}")

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {path}")

    native_fps = info.fps if info.fps > 0 else 30.0
    step = max(1, int(round(native_fps / max(sample_fps, 1e-6))))
    indices = list(range(0, max(info.total_frames, 1), step))
    if len(indices) > max_samples:
        if max_samples <= 1:
            indices = indices[:1]
        else:
            stride = (len(indices) - 1) / (max_samples - 1)
            indices = [indices[round(i * stride)] for i in range(max_samples)]

    samples: list[SampledFrame] = []
    prev_feature = None
    for frame_idx in indices:
        if seek_sample:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame_idx))
        ok, frame = cap.read()
        if not ok:
            continue
        feature = frame_feature(frame)
        diff = 0.0 if prev_feature is None else 1.0 - float(feature @ prev_feature)
        prev_feature = feature
        samples.append(
            SampledFrame(
                frame_idx=int(frame_idx),
                timestamp_sec=float(frame_idx / native_fps),
                frame_bgr=frame,
                feature=feature,
                diff_score=float(max(diff, 0.0)),
            )
        )
    cap.release()
    return info, samples
