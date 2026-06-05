from __future__ import annotations

from pathlib import Path


def write_keyframe_report(path: Path, video_name: str, keyframes: list[dict], rel_image_dir: str, metrics: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cards = []
    for item in keyframes:
        img = f"{rel_image_dir}/{item['image']}"
        cards.append(
            f"<figure><img src='{img}' alt='frame {item['frame_idx']}'><figcaption>"
            f"#{item['rank']} frame={item['frame_idx']} time={item['timestamp_sec']}s<br>"
            f"{', '.join(item.get('sources', []))}</figcaption></figure>"
        )
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{video_name} keyframe report</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 24px; color: #1f2937; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 14px; }}
figure {{ margin: 0; border: 1px solid #d1d5db; padding: 8px; border-radius: 6px; }}
img {{ width: 100%; height: 140px; object-fit: cover; display: block; }}
figcaption {{ font-size: 12px; line-height: 1.35; margin-top: 6px; }}
pre {{ background: #f3f4f6; padding: 12px; overflow: auto; }}
</style>
</head>
<body>
<h1>{video_name}</h1>
<pre>{metrics}</pre>
<div class="grid">
{''.join(cards)}
</div>
</body>
</html>"""
    path.write_text(html, encoding="utf-8")


def write_benchmark_report(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = "".join(f"<th>{h}</th>" for h in (rows[0].keys() if rows else ["status"]))
    body = "\n".join("<tr>" + "".join(f"<td>{v}</td>" for v in row.values()) + "</tr>" for row in rows)
    if not rows:
        body = "<tr><td>Please put .mp4 files into orinKeyframe_01/videos and rerun benchmark.</td></tr>"
    path.write_text(f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Benchmark report</title>
<style>body{{font-family:Arial,sans-serif;margin:24px}}table{{border-collapse:collapse}}td,th{{border:1px solid #ccc;padding:6px 8px}}</style>
</head><body><h1>Benchmark report</h1><table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table></body></html>""", encoding="utf-8")
