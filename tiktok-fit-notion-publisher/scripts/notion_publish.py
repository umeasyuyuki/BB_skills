#!/usr/bin/env python3
"""One-command Notion publish helper for content documents.

Supported source formats:
- JSON package (ready for Notion save)
- Markdown/text file (auto-convert to package JSON)

Flow:
1) pick source (explicit or latest package JSON in inbox)
2) if markdown/text, convert into package JSON
3) if script section exists, auto-approve by default
4) run notion_save_document.py
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
SAVER = SCRIPT_DIR / "notion_save_document.py"
DEFAULT_TARGET_CONFIG = SKILL_DIR / ".notion-target.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Quick publish document package to Notion")
    parser.add_argument("source", nargs="?", help="Source path (JSON package or markdown file). Supports @~/... form")
    parser.add_argument("--input", type=Path, help="Source path (JSON package or markdown file)")
    parser.add_argument("--inbox-dir", type=Path, default=Path("data/notion-inbox"), help="Inbox directory")
    parser.add_argument("--approve", action="store_true", help="Auto-approve before save")
    parser.add_argument("--no-auto-approve", action="store_true", help="Disable automatic approval from script section")
    parser.add_argument("--note", default="", help="Optional review note when auto-approving")
    parser.add_argument("--dry-run", action="store_true", help="Validate only; do not write to Notion")
    parser.add_argument("--property-map", type=Path, help="Optional property map JSON")
    parser.add_argument("--force", action="store_true", help="Save even when approved=false")
    parser.add_argument("--target-config", type=Path, default=DEFAULT_TARGET_CONFIG, help="Path to local Notion target config JSON")
    parser.add_argument("--ignore-target-config", action="store_true", help="Ignore local Notion target config file")
    parser.add_argument("--notion-token", default="", help="Override NOTION_API_KEY")
    parser.add_argument("--notion-database-id", default="", help="Override target database id")
    parser.add_argument("--notion-data-source-id", default="", help="Override target data source id")
    parser.add_argument("--title", default="", help="Override title for markdown source")
    parser.add_argument("--theme", default="", help="Override theme for markdown source")
    parser.add_argument("--workflow", default="auto", help="Workflow label for markdown source")
    parser.add_argument("--source-url", default="", help="Optional source URL")
    parser.add_argument("--tags", nargs="*", default=[], help="Tags for markdown source package")
    parser.add_argument("--output", type=Path, help="Optional output JSON path")
    return parser.parse_args()


def write_result(output_path: Path | None, payload: dict[str, Any]) -> None:
    content = json.dumps(payload, ensure_ascii=False, indent=2)
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
    else:
        print(content)


def pick_latest_json(inbox_dir: Path) -> Path | None:
    if not inbox_dir.exists():
        return None
    files = [p for p in inbox_dir.glob("*.json") if p.is_file()]
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def resolve_source_path(raw: str | Path | None) -> Path | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    # Antigravity mentions may look like @~/path/to/file.md
    if text.startswith("@"):
        text = text[1:]
    return Path(text).expanduser()


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("JSONのルートはオブジェクトである必要があります")
    return data


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def slugify(text: str) -> str:
    value = text.strip().lower()
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"[^a-z0-9\-ぁ-んァ-ン一-龥]", "", value)
    return value[:80] or "document-package"


def detect_first_heading(markdown: str) -> str:
    for line in markdown.splitlines():
        m = re.match(r"^\s*#{1,3}\s+(.+?)\s*$", line)
        if m:
            return m.group(1).strip()
    for line in markdown.splitlines():
        text = line.strip()
        if text:
            return text[:80]
    return ""


def map_heading_to_section(heading: str) -> str | None:
    h = heading.lower()
    if heading.startswith("画像"):
        return None
    if any(k in heading for k in ["タイトル改善案", "タイトル案", "タイトル提案"]) or "title" in h:
        return "title_ideas"
    if any(k in heading for k in ["調査", "エビデンス"]) or "research" in h:
        return "research"
    if any(k in heading for k in ["評価", "チェック", "薬機", "法リスク"]) or "compliance" in h or "check" in h:
        return "compliance_check"
    if any(k in heading for k in ["台本", "原稿", "投稿文", "キャプション"]) or "script" in h or "caption" in h:
        return "script"
    if any(k in heading for k in ["総まとめ表画像", "まとめ画像"]) or "summary_image" in h:
        return "summary_image"
    if any(k in heading for k in ["総まとめ", "比較表", "サマリー表", "素材管理表", "一覧表"]) or "summary" in h or "table" in h:
        return "summary_table"
    if any(k in heading for k in ["根拠", "引用", "参考", "リンク"]) or "reference" in h:
        return "references"
    return None


def parse_markdown_sections(markdown: str) -> dict[str, str]:
    mapped: dict[str, str] = {
        "body": "",
        "title_ideas": "",
        "research": "",
        "compliance_check": "",
        "script": "",
        "summary_table": "",
        "summary_image": "",
        "references": "",
    }
    lines = markdown.splitlines()
    # Each fragment: (heading_text, heading_level, body_text)
    current_heading = ""
    current_level = 0
    bucket: list[str] = []
    fragments: list[tuple[str, int, str]] = []

    def flush() -> None:
        nonlocal current_heading, bucket
        body = "\n".join(bucket).strip()
        # Always record the fragment if there is a heading, even with empty body.
        # This ensures section headings like "## 台本" set last_key properly.
        if current_heading or body:
            fragments.append((current_heading, current_level, body))
        bucket = []

    for line in lines:
        m = re.match(r"^(\s*)(#{1,3})\s+(.+?)\s*$", line)
        if m:
            flush()
            current_heading = m.group(3).strip()
            current_level = len(m.group(2))
            continue
        bucket.append(line)
    flush()

    last_key: str | None = None
    for heading, level, body in fragments:
        # Only h1/h2 headings are checked for section mapping
        if level <= 2:
            key = map_heading_to_section(heading)
            if key:
                last_key = key
                if body:
                    if mapped[key]:
                        mapped[key] = f"{mapped[key]}\n\n{body}".strip()
                    else:
                        mapped[key] = body
                continue
            # Unmatched h1/h2 -> accumulate into "body" with heading preserved
            last_key = "body"
            prefix = "#" * level
            section_text = f"{prefix} {heading}\n{body}".strip() if heading else body
            if mapped["body"]:
                mapped["body"] = f"{mapped['body']}\n\n{section_text}"
            else:
                mapped["body"] = section_text
            continue
        # h3 sub-headings (or unmatched h2) -> append to most recent parent section
        if last_key and body:
            prefix = "#" * level if level else "###"
            section_heading = f"{prefix} {heading}" if heading else ""
            addition = f"{section_heading}\n{body}".strip()
            if mapped[last_key]:
                mapped[last_key] = f"{mapped[last_key]}\n\n{addition}"
            else:
                mapped[last_key] = addition

    if not any(mapped.values()):
        # Fallback: store whole text as script if no recognizable headings exist.
        mapped["script"] = markdown.strip()
    return mapped


def build_package_from_markdown(source_path: Path, args: argparse.Namespace) -> Path:
    content = source_path.read_text(encoding="utf-8")
    title = args.title.strip() or source_path.stem
    theme = args.theme.strip() or title

    pkg = {
        "title": title,
        "theme": theme,
        "workflow": args.workflow,
        "status": "承認済み",
        "approved": True,
        "created_at": datetime.now(timezone.utc).date().isoformat(),
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "source_url": args.source_url,
        "tags": args.tags or [],
        "sections": parse_markdown_sections(content),
    }

    args.inbox_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = args.inbox_dir / f"{slugify(source_path.stem)}-{ts}.json"
    save_json(out, pkg)
    return out


def auto_approve_if_needed(path: Path, note: str) -> tuple[bool, str]:
    data = load_json(path)
    if bool(data.get("approved", False)):
        return False, "already_approved"

    data["approved"] = True
    data["status"] = "承認済み"
    data["approved_at"] = datetime.now(timezone.utc).isoformat()
    if note:
        data["review_note"] = note
    save_json(path, data)
    return True, "auto_approved"


def has_script_section(pkg: dict[str, Any]) -> bool:
    sections = pkg.get("sections")
    if not isinstance(sections, dict):
        return False
    script = sections.get("script")
    return bool(str(script).strip()) if script is not None else False


def run_saver(target: Path, args: argparse.Namespace) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(SAVER), "--input", str(target)]
    if args.dry_run:
        cmd.append("--dry-run")
    if args.property_map:
        cmd.extend(["--property-map", str(args.property_map)])
    if args.target_config:
        cmd.extend(["--target-config", str(args.target_config)])
    if args.ignore_target_config:
        cmd.append("--ignore-target-config")
    if args.notion_token.strip():
        cmd.extend(["--notion-token", args.notion_token.strip()])
    if args.notion_database_id.strip():
        cmd.extend(["--notion-database-id", args.notion_database_id.strip()])
    if args.notion_data_source_id.strip():
        cmd.extend(["--notion-data-source-id", args.notion_data_source_id.strip()])
    if args.force:
        cmd.append("--force")
    return subprocess.run(cmd, capture_output=True, text=True)


def main() -> int:
    args = parse_args()

    try:
        if not SAVER.exists():
            write_result(args.output, {"ok": False, "error": f"Saver script not found: {SAVER}"})
            return 1

        source = args.input if args.input else resolve_source_path(args.source)
        target = resolve_source_path(source)
        if not target:
            target = pick_latest_json(args.inbox_dir)
            if not target:
                write_result(args.output, {
                    "ok": False,
                    "error": "保存対象JSONが見つかりません。--input を指定するか data/notion-inbox にJSONを置いてください",
                })
                return 1

        if not target.exists():
            write_result(args.output, {"ok": False, "error": f"対象ファイルが存在しません: {target}"})
            return 1

        created_from: str | None = None
        ext = target.suffix.lower()
        if ext in {".md", ".markdown", ".txt"}:
            package_json = build_package_from_markdown(target, args)
            created_from = str(target)
            target = package_json
        elif ext != ".json":
            write_result(args.output, {
                "ok": False,
                "error": "サポート対象外の拡張子です。.json / .md / .markdown / .txt を指定してください",
                "input": str(target),
            })
            return 1

        approval_action = "none"
        pkg = load_json(target)
        should_auto_approve = args.approve or (has_script_section(pkg) and not args.no_auto_approve)
        if should_auto_approve:
            changed, approval_action = auto_approve_if_needed(target, args.note)
            if changed:
                approval_action = "auto_approved"
            pkg = load_json(target)
        approved = bool(pkg.get("approved", False))

        proc = run_saver(target, args)
        saver_json: dict[str, Any]
        try:
            saver_json = json.loads(proc.stdout) if proc.stdout.strip() else {}
            if not isinstance(saver_json, dict):
                saver_json = {"raw": proc.stdout.strip()}
        except Exception:  # noqa: BLE001
            saver_json = {"raw": proc.stdout.strip()}

        ok = proc.returncode == 0 and bool(saver_json.get("ok", False) or args.dry_run)
        write_result(args.output, {
            "ok": ok,
            "input": str(target),
            "created_from": created_from,
            "approval_action": approval_action,
            "approved": approved,
            "dry_run": args.dry_run,
            "saver_returncode": proc.returncode,
            "saver_result": saver_json,
            "stderr": proc.stderr.strip(),
        })
        return 0 if ok else 1
    except Exception as exc:  # noqa: BLE001
        write_result(args.output, {"ok": False, "error": str(exc)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
