from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


def read_order(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def create_link_or_copy(src: Path, dst: Path, mode: str) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        dst.unlink()
    if mode == "copy":
        shutil.copy2(src, dst)
        return "copied"
    try:
        os.symlink(src.resolve(), dst)
        return "linked"
    except Exception:
        shutil.copy2(src, dst)
        return "copied_fallback"


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare downloaded X-Lebench videos in user-defined order.")
    parser.add_argument("--video_dir", default="datasets/X-Lebench数据集（部分）/Ego4D/v2/full_scale")
    parser.add_argument("--order_file", default="datasets/video_order_user.png_list.txt")
    parser.add_argument("--out_dir", default="datasets/xlebench_ordered_videos")
    parser.add_argument("--mode", choices=["manifest", "symlink", "copy"], default="manifest")
    args = parser.parse_args()

    video_dir = Path(args.video_dir)
    order = read_order(Path(args.order_file))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[str] = []
    missing: list[str] = []
    for idx, uid in enumerate(order, start=1):
        src = video_dir / f"{uid}.mp4"
        if not src.exists():
            missing.append(uid)
            rows.append(f"{idx:03d}\tMISSING\t{uid}\t{src}")
            continue
        ordered_name = f"{idx:03d}_{uid}.mp4"
        if args.mode in {"symlink", "copy"}:
            status = create_link_or_copy(src, out_dir / ordered_name, args.mode)
            rows.append(f"{idx:03d}\t{status}\t{uid}\t{out_dir / ordered_name}")
        else:
            rows.append(f"{idx:03d}\tfound\t{uid}\t{src}")

    manifest = out_dir / "ordered_manifest.tsv"
    manifest.write_text("\n".join(rows) + "\n", encoding="utf-8")
    missing_path = out_dir / "missing_video_ids.txt"
    missing_path.write_text("\n".join(missing) + ("\n" if missing else ""), encoding="utf-8")

    print(f"Ordered manifest: {manifest}")
    print(f"Missing videos: {len(missing)}")
    if missing:
        print(f"Missing list: {missing_path}")


if __name__ == "__main__":
    main()
