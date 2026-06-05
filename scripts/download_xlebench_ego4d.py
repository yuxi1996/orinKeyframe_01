from __future__ import annotations

import argparse
import configparser
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_DATASET_ROOT = Path("datasets") / "xlebench_partial"
DEFAULT_ANNOTATION = DEFAULT_DATASET_ROOT / "simulation_0120dffb_0d0b4c6b_annotation.json"
DEFAULT_OUTPUT_DIR = DEFAULT_DATASET_ROOT / "Ego4D"


def load_video_ids(annotation_path: Path, order_file: Path | None = None) -> list[str]:
    data = json.loads(annotation_path.read_text(encoding="utf-8"))
    ids: list[str] = []

    def add(uid: str | None) -> None:
        if uid and uid not in ids:
            ids.append(uid)

    for item in data.get("simulations", []):
        add(item.get("video_uid"))

    if not ids:
        def walk(obj) -> None:
            if isinstance(obj, dict):
                add(obj.get("video_uid"))
                for value in obj.values():
                    walk(value)
            elif isinstance(obj, list):
                for value in obj:
                    walk(value)

        walk(data)

    if order_file and order_file.exists():
        ordered = [line.strip() for line in order_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        order_rank = {uid: i for i, uid in enumerate(ordered)}
        ids = sorted(ids, key=lambda uid: order_rank.get(uid, 10**9))
    return ids


def _config_has_profile(path: Path, profile_name: str) -> bool:
    parser = configparser.ConfigParser()
    parser.read(path, encoding="utf-8")
    candidates = {profile_name, f"profile {profile_name}"}
    return any(section in candidates for section in parser.sections())


def validate_aws_inputs(args: argparse.Namespace) -> None:
    config_path = Path(args.aws_config).expanduser() if args.aws_config else Path.home() / ".aws" / "config"
    credentials_path = Path(args.aws_credentials).expanduser() if args.aws_credentials else Path.home() / ".aws" / "credentials"
    profile_name = args.aws_profile or os.environ.get("AWS_PROFILE") or "default"

    missing = [str(p) for p in [config_path, credentials_path] if not p.exists()]
    if missing:
        raise SystemExit(
            "Ego4D download needs real AWS/Ego4D credential files. These paths do not exist:\n"
            + "\n".join(f"  {p}" for p in missing)
            + "\n\nDo not use placeholder paths like /path/to/aws/config.\n"
            "Use real files, for example:\n"
            "  bash scripts/orin_auto_setup_download_test.sh --aws-config ~/.aws/config --aws-credentials ~/.aws/credentials\n"
            "Or first inspect IDs only:\n"
            "  python scripts/download_xlebench_ego4d.py --dry_run"
        )

    if not _config_has_profile(config_path, profile_name):
        raise SystemExit(
            f"AWS config file exists, but profile '{profile_name}' was not found in: {config_path}\n"
            "For the default profile, the config should contain a [default] section.\n"
            "For a named profile, pass --aws_profile your_profile_name."
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Download X-Lebench related Ego4D full_scale videos on Orin.")
    parser.add_argument("--annotation", default=str(DEFAULT_ANNOTATION))
    parser.add_argument("--order_file", default=str(Path("datasets") / "video_order_user.png_list.txt"))
    parser.add_argument("--output_directory", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--aws_config", default=None, help="Optional AWS config path for Ego4D CLI.")
    parser.add_argument("--aws_credentials", default=None, help="Optional AWS credentials path for Ego4D CLI.")
    parser.add_argument("--aws_profile", default=None, help="AWS profile name for Ego4D CLI. Default uses Ego4D CLI default.")
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()

    annotation = Path(args.annotation)
    if not annotation.exists():
        raise SystemExit(f"Annotation JSON not found: {annotation}")

    output_dir = Path(args.output_directory)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.aws_config:
        os.environ["AWS_CONFIG_FILE"] = str(Path(args.aws_config).expanduser())
    if args.aws_credentials:
        os.environ["AWS_SHARED_CREDENTIALS_FILE"] = str(Path(args.aws_credentials).expanduser())
    if args.aws_profile:
        os.environ["AWS_PROFILE"] = args.aws_profile

    video_ids = load_video_ids(annotation, Path(args.order_file))
    if not video_ids:
        raise SystemExit("No video_uid values found in annotation JSON.")

    cmd = [
        "ego4d",
        "--output_directory",
        str(output_dir),
        "--datasets",
        "full_scale",
        "--video_uids",
        *video_ids,
        "-y",
    ]
    print(f"Video IDs: {len(video_ids)}")
    print("\n".join(video_ids))
    print("Command:")
    print(" ".join(cmd))
    if args.dry_run:
        return
    validate_aws_inputs(args)
    if shutil.which("ego4d") is None:
        raise SystemExit("ego4d CLI not found. Install it on Orin first, for example: python3 -m pip install ego4d")
    sys.exit(subprocess.run(cmd).returncode)


if __name__ == "__main__":
    main()
