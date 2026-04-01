#!/usr/bin/env python3
"""Batch autosave document-package JSON files into Notion."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List

SCRIPT_DIR = Path(__file__).resolve().parent
SAVER = SCRIPT_DIR / "notion_save_document.py"


def run_one(input_path: Path, dry_run: bool, extra_args: List[str]) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(SAVER), "--input", str(input_path)]
    if dry_run:
        cmd.append("--dry-run")
    cmd.extend(extra_args)
    return subprocess.run(cmd, capture_output=True, text=True)


def move_with_timestamp(src: Path, dst_dir: Path) -> Path:
    dst_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = dst_dir / f"{src.stem}_{ts}{src.suffix}"
    shutil.move(str(src), str(dst))
    return dst


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Autosave content package JSON files to Notion")
    parser.add_argument("--input", type=Path, help="Single JSON file to process")
    parser.add_argument("--inbox-dir", type=Path, default=Path("data/notion-inbox"), help="Directory with JSON files")
    parser.add_argument("--sent-dir", type=Path, default=Path("data/notion-sent"), help="Directory for successful files")
    parser.add_argument("--failed-dir", type=Path, default=Path("data/notion-failed"), help="Directory for failed files")
    parser.add_argument("--dry-run", action="store_true", help="Validate only; do not write to Notion")
    parser.add_argument("--keep-files", action="store_true", help="Do not move input files after processing")
    parser.add_argument("--property-map", type=Path, help="Path to Notion property map JSON")
    parser.add_argument("--force", action="store_true", help="Pass --force to saver")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not SAVER.exists():
        print(json.dumps({
            "ok": False,
            "error": f"Saver script not found: {SAVER}"
        }, ensure_ascii=False, indent=2))
        return 1

    targets: List[Path]
    if args.input:
        targets = [args.input]
    else:
        targets = sorted(args.inbox_dir.glob("*.json"))

    if not targets:
        print(json.dumps({
            "ok": True,
            "processed": 0,
            "message": "対象JSONが見つかりませんでした"
        }, ensure_ascii=False, indent=2))
        return 0

    extra_args: List[str] = []
    if args.property_map:
        extra_args.extend(["--property-map", str(args.property_map)])
    if args.force:
        extra_args.append("--force")

    results = []
    ok_count = 0
    fail_count = 0
    skip_count = 0

    for target in targets:
        proc = run_one(target, args.dry_run, extra_args)
        success = proc.returncode == 0

        moved_to = None
        if not args.keep_files and not args.dry_run:
            if success:
                moved_to = str(move_with_timestamp(target, args.sent_dir))
            else:
                moved_to = str(move_with_timestamp(target, args.failed_dir))

        results.append({
            "input": str(target),
            "ok": success,
            "skipped": False,
            "returncode": proc.returncode,
            "moved_to": moved_to,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        })

        if success:
            ok_count += 1
        else:
            fail_count += 1

    print(json.dumps({
        "ok": fail_count == 0,
        "dry_run": args.dry_run,
        "processed": len(targets),
        "success": ok_count,
        "skipped": skip_count,
        "failed": fail_count,
        "results": results,
    }, ensure_ascii=False, indent=2))

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
