#!/usr/bin/env python3
"""Create a document package JSON from markdown files."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^a-z0-9\-ぁ-んァ-ン一-龥]", "", text)
    return text[:80] or "document-package"


def read_file(path: str | None) -> str:
    if not path:
        return ""
    return Path(path).read_text(encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create document package JSON")
    parser.add_argument("--title", required=True)
    parser.add_argument("--theme", required=True)
    parser.add_argument("--workflow", required=True)
    parser.add_argument("--source-url", default="")
    parser.add_argument("--tags", nargs="*", default=[])
    parser.add_argument("--research-file")
    parser.add_argument("--compliance-file")
    parser.add_argument("--script-file")
    parser.add_argument("--summary-table-file")
    parser.add_argument("--title-ideas-file")
    parser.add_argument("--summary-image-file")
    parser.add_argument("--references-file")
    parser.add_argument("--out")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    created_at = datetime.now(timezone.utc).date().isoformat()

    pkg = {
        "title": args.title,
        "theme": args.theme,
        "workflow": args.workflow,
        "status": "承認済み",
        "approved": True,
        "created_at": created_at,
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "source_url": args.source_url,
        "tags": args.tags,
        "sections": {
            "title_ideas": read_file(args.title_ideas_file),
            "research": read_file(args.research_file),
            "compliance_check": read_file(args.compliance_file),
            "script": read_file(args.script_file),
            "summary_table": read_file(args.summary_table_file),
            "summary_image": read_file(args.summary_image_file),
            "references": read_file(args.references_file),
        },
    }

    if args.out:
        out = Path(args.out)
    else:
        slug = slugify(args.title)
        out = Path("data/notion-inbox") / f"{slug}.json"

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(pkg, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "ok": True,
        "output": str(out),
        "status": pkg["status"],
        "approved": pkg["approved"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
