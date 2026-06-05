from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from .feature_utils import SampledFrame

os.environ.setdefault("YOLO_CONFIG_DIR", str(Path("outputs") / "logs" / "ultralytics_config"))

PERSON_CLASSES = {"person"}
OBJECT_CLASSES = {
    "bicycle", "car", "motorcycle", "bus", "truck", "backpack", "handbag",
    "suitcase", "sports ball", "bottle", "cup", "fork", "knife", "spoon",
    "bowl", "chair", "couch", "bed", "dining table", "tv", "laptop",
    "mouse", "remote", "keyboard", "cell phone", "book", "clock", "vase",
    "potted plant", "microwave", "oven", "sink", "refrigerator",
}


def ocr_proxy_score(frame_bgr: np.ndarray) -> float:
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    small = cv2.resize(gray, (320, 180), interpolation=cv2.INTER_AREA)
    grad_x = cv2.Sobel(small, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(small, cv2.CV_32F, 0, 1, ksize=3)
    mag = cv2.magnitude(grad_x, grad_y)
    edge_density = float((mag > 45).mean())
    return min(edge_density * 2.0, 1.0)


def clip_proxy_score(frame_bgr: np.ndarray) -> float:
    small = cv2.resize(frame_bgr, (96, 54), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    sat = float(hsv[:, :, 1].mean() / 255.0)
    val_std = float(hsv[:, :, 2].std() / 128.0)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    edge = float(cv2.Canny(gray, 80, 160).mean() / 255.0)
    return 0.4 * sat + 0.4 * min(val_std, 1.0) + 0.2 * edge


def load_yolo(weights_path: Path, enabled: bool) -> tuple[Any | None, str]:
    if not enabled:
        return None, "YOLO disabled by config."
    if not weights_path.exists():
        return None, "YOLO weights not found, fallback to non-YOLO keyframe extraction."
    try:
        from ultralytics import YOLO  # type: ignore

        return YOLO(str(weights_path)), "YOLO enabled."
    except Exception as exc:
        return None, f"YOLO unavailable ({exc}), fallback to non-YOLO keyframe extraction."


def score_task_channels(samples: list[SampledFrame], model: Any | None, max_yolo_frames: int) -> list[dict]:
    if not samples:
        return []
    positions = list(range(len(samples)))
    if model is not None and len(positions) > max_yolo_frames:
        positions = [int(i) for i in np.linspace(0, len(samples) - 1, max_yolo_frames, dtype=int)]

    rows: list[dict] = []
    yolo_pos = set(positions) if model is not None else set()
    for pos, sample in enumerate(samples):
        person_score = 0.0
        object_score = 0.0
        small_object_score = 0.0
        classes: list[str] = []
        if model is not None and pos in yolo_pos:
            result = model(sample.frame_bgr, verbose=False, imgsz=640)[0]
            h, w = sample.frame_bgr.shape[:2]
            frame_area = max(1, h * w)
            if result.boxes is not None:
                for i in range(len(result.boxes)):
                    cls_id = int(result.boxes.cls[i])
                    name = result.names[cls_id]
                    conf = float(result.boxes.conf[i])
                    if conf < 0.20:
                        continue
                    x1, y1, x2, y2 = result.boxes.xyxy[i].tolist()
                    area_ratio = max(0.0, (x2 - x1) * (y2 - y1) / frame_area)
                    if name in PERSON_CLASSES:
                        person_score += 3.0 * conf * (1.0 + min(area_ratio * 4.0, 2.0))
                        classes.append(name)
                    elif name in OBJECT_CLASSES:
                        object_score += 2.0 * conf * (1.0 + min(area_ratio * 4.0, 2.0))
                        if area_ratio < 0.02:
                            small_object_score += 3.0 * conf
                        classes.append(name)
        rows.append({
            "frame_idx": sample.frame_idx,
            "timestamp_sec": sample.timestamp_sec,
            "person_score": float(person_score),
            "object_score": float(object_score),
            "small_object_score": float(small_object_score),
            "ocr_proxy_score": float(ocr_proxy_score(sample.frame_bgr)),
            "clip_proxy_score": float(clip_proxy_score(sample.frame_bgr)),
            "classes": sorted(set(classes)),
        })
    return rows
