from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class SampledFrame:
    frame_idx: int
    timestamp_sec: float
    frame_bgr: np.ndarray
    feature: np.ndarray
    diff_score: float


def frame_feature(frame_bgr: np.ndarray) -> np.ndarray:
    """Small deterministic feature: HSV histogram plus low-res grayscale layout."""
    small = cv2.resize(frame_bgr, (64, 36), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [16, 8], [0, 180, 0, 256]).flatten()
    hist = hist / max(float(np.linalg.norm(hist)), 1e-8)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    layout = cv2.resize(gray, (8, 8), interpolation=cv2.INTER_AREA).flatten()
    vec = np.concatenate([hist.astype(np.float32), layout.astype(np.float32)])
    return vec / max(float(np.linalg.norm(vec)), 1e-8)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom <= 1e-12:
        return 0.0
    return float(np.dot(a, b) / denom)


def simple_kmeans(features: np.ndarray, k: int, max_iter: int = 25) -> list[int]:
    """Return representative row indices with a dependency-free KMeans."""
    n = len(features)
    if n == 0 or k <= 0:
        return []
    if k >= n:
        return list(range(n))

    centers = features[np.linspace(0, n - 1, k, dtype=int)].copy()
    labels = np.zeros(n, dtype=np.int32)
    for _ in range(max_iter):
        dists = ((features[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
        new_labels = dists.argmin(axis=1)
        if np.array_equal(labels, new_labels):
            break
        labels = new_labels
        for i in range(k):
            members = features[labels == i]
            if len(members):
                centers[i] = members.mean(axis=0)

    reps: list[int] = []
    for i in range(k):
        member_idx = np.where(labels == i)[0]
        if len(member_idx) == 0:
            continue
        center = centers[i]
        nearest = member_idx[((features[member_idx] - center) ** 2).sum(axis=1).argmin()]
        reps.append(int(nearest))
    return sorted(set(reps))
