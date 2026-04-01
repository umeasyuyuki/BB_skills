#!/usr/bin/env python3
"""Approve/reject content package JSON before Notion save."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Approve or reject document package")
    parser.add_argument("--input", required=True, help="Package JSON path")
    parser.add_argument("--output", help="Output JSON path (default: overwrite input)")
    parser.add_argument("--approve", action="store_true", help="Set approved=true")
    parser.add_argument("--reject", action="store_true", help="Set approved=false and rejected status")
    parser.add_argument("--note", default="", help="Optional reviewer note")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    in_path = Path(args.input)
    data = json.loads(in_path.read_text(encoding="utf-8"))

    if args.approve and args.reject:
        raise SystemExit("--approve と --reject は同時指定できません")

    now = datetime.now(timezone.utc).isoformat()

    if args.approve:
        data["approved"] = True
        data["status"] = "承認済み"
        data["approved_at"] = now
    elif args.reject:
        data["approved"] = False
        data["status"] = "却下"
        data["rejected_at"] = now
    else:
        data["status"] = data.get("status", "承認済み")

    if args.note:
        data["review_note"] = args.note

    out_path = Path(args.output) if args.output else in_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "ok": True,
        "input": str(in_path),
        "output": str(out_path),
        "status": data.get("status"),
        "approved": data.get("approved", False),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
