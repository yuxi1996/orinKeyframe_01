# Algorithm Design

The project wraps the current keyframe benchmark idea into a portable, file-only benchmark that runs on Windows and Jetson Orin.

Pipeline:

```text
video file
-> sample at sample_fps
-> extract lightweight HSV/layout features
-> select KMeans representatives
-> add Uniform coverage candidates
-> optionally score sampled frames with YOLO person/object/small-object channels
-> add deterministic OCR/CLIP proxy channels
-> fuse candidates by channel quotas
-> remove near-time and globally similar duplicates
-> export images, JSON, HTML, CSV metrics
```

The default quota split is task-aware:

| Channel | Ratio |
|---|---:|
| KMeans | 50% |
| Uniform | 15% |
| YOLO person | 10% |
| YOLO object | 12% |
| YOLO small object | 8% |
| OCR/CLIP proxy | remaining budget |

YOLO is optional. When `weights/yolo26n.pt` is absent or `ultralytics` cannot be imported, the code logs the fallback and continues with KMeans, Uniform, proxy scores, and dedup.

The OCR/CLIP proxy channels are lightweight deterministic placeholders. They are designed so true OCR or true CLIP can replace them without changing the output schema.

Dedup uses feature cosine similarity:

- near-time duplicate: frame distance below `dedup_min_gap_frames` and similarity above `dedup_threshold`
- global duplicate: similarity above `0.997`

This is meant to reduce repeated static scenes before images and JSON are written.
