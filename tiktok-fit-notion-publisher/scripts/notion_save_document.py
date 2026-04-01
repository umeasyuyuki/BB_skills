#!/usr/bin/env python3
"""Save approved content documents to Notion database/data source.

This script is designed for content pipelines (research -> compliance -> script -> approval).
No engagement metrics are required.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DEFAULT_TARGET_CONFIG = SKILL_DIR / ".notion-target.json"

DEFAULT_PROPERTY_MAP = {
    "title": "Name",
    "theme": "Theme",
    "workflow": "Workflow",
    "status": "Status",
    "approved": "Approved",
    "created_at": "Created At",
    "approved_at": "Approved At",
    "source_url": "Source URL",
    "tags": "Tags",
}

CANONICAL_PROPERTY_ALIASES = {
    "title": ["Name", "名前", "タイトル", "Title"],
    "theme": ["Theme", "テーマ"],
    "workflow": ["Workflow", "ワークフロー", "投稿タイプ"],
    "status": ["Status", "ステータス"],
    "approved": ["Approved", "承認済み", "承認"],
    "created_at": ["Created At", "作成日", "作成日時"],
    "approved_at": ["Approved At", "承認日", "承認日時"],
    "source_url": ["Source URL", "ソースURL", "URL"],
    "tags": ["Tags", "タグ"],
}

SECTION_ORDER = [
    ("body", ""),
    ("title_ideas", "タイトル改善案"),
    ("research", "調査"),
    ("compliance_check", "評価チェック"),
    ("script", "台本"),
    ("summary_table", "素材管理表"),
    ("summary_image", "総まとめ表画像"),
    ("references", "根拠リンク"),
]

BR_TAG_RE = re.compile(r"(?i)<br\s*/?>")
HTML_TAG_RE = re.compile(r"(?is)</?(?!https?://)[a-z][^>]*>")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Save approved content package to Notion")
    parser.add_argument("--input", required=True, help="Path to document package JSON")
    parser.add_argument("--property-map", help="Optional JSON file mapping canonical keys to Notion property names")
    parser.add_argument("--force", action="store_true", help="Allow save even when approved=false")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print payload without Notion write")
    parser.add_argument("--output", help="Optional path to write result JSON")
    parser.add_argument("--target-config", default=str(DEFAULT_TARGET_CONFIG), help="Path to local Notion target config JSON")
    parser.add_argument("--ignore-target-config", action="store_true", help="Ignore local target config file")
    parser.add_argument("--notion-token")
    parser.add_argument("--notion-database-id")
    parser.add_argument("--notion-data-source-id")
    parser.add_argument("--notion-version", default="2025-09-03")
    args = parser.parse_args()
    apply_notion_credentials(args)
    return args


def load_target_config(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        return {}
    data = load_json(path)
    return data if isinstance(data, dict) else {}


def pick_credential(
    cli_value: str | None,
    config_value: Any,
    env_key: str,
) -> str | None:
    if cli_value == "CLEAR" or cli_value == "none":
        return None
    if cli_value:
        return str(cli_value).strip()
    if isinstance(config_value, str) and config_value.strip():
        return config_value.strip()
    env_val = os.getenv(env_key)
    if isinstance(env_val, str) and env_val.strip():
        return env_val.strip()
    return None


def apply_notion_credentials(args: argparse.Namespace) -> None:
    cfg: dict[str, Any] = {}
    if not args.ignore_target_config:
        cfg = load_target_config(args.target_config)

    args.notion_token = pick_credential(
        args.notion_token,
        cfg.get("notion_api_key"),
        "NOTION_API_KEY",
    )
    args.notion_database_id = pick_credential(
        args.notion_database_id,
        cfg.get("notion_database_id"),
        "NOTION_DATABASE_ID",
    )
    args.notion_data_source_id = pick_credential(
        args.notion_data_source_id,
        cfg.get("notion_data_source_id"),
        "NOTION_DATA_SOURCE_ID",
    )


def load_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Input JSON must be object")
    return data


def load_property_map(path: str | None) -> dict[str, str]:
    if not path:
        return dict(DEFAULT_PROPERTY_MAP)
    data = load_json(path)
    if not all(isinstance(k, str) and isinstance(v, str) for k, v in data.items()):
        raise ValueError("Property map must be object with string key/value")
    merged = dict(DEFAULT_PROPERTY_MAP)
    merged.update(data)
    return merged


def notion_headers(token: str, notion_version: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": notion_version,
    }


def notion_get(url: str, headers: dict[str, str]) -> dict[str, Any]:
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Notion API error {exc.code}: {detail}") from exc


def notion_request(url: str, method: str, headers: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, headers=headers, data=body, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Notion API error {exc.code}: {detail}") from exc


def normalize_notion_id(value: str | None) -> str:
    if not value:
        return ""
    return str(value).replace("-", "").strip().lower()


def same_notion_id(left: str | None, right: str | None) -> bool:
    return bool(normalize_notion_id(left) and normalize_notion_id(left) == normalize_notion_id(right))


def fetch_database_metadata(token: str, database_id: str, notion_version: str) -> dict[str, Any]:
    headers = notion_headers(token, notion_version)
    return notion_get(f"https://api.notion.com/v1/databases/{database_id}", headers)


def extract_data_source_ids(database_metadata: dict[str, Any]) -> list[str]:
    data_sources = database_metadata.get("data_sources") or []
    if not isinstance(data_sources, list):
        return []
    ids: list[str] = []
    for item in data_sources:
        if not isinstance(item, dict):
            continue
        ds_id = item.get("id")
        if isinstance(ds_id, str) and ds_id.strip():
            ids.append(ds_id.strip())
    return ids


def resolve_data_source_id(token: str, database_id: str, notion_version: str) -> str | None:
    data = fetch_database_metadata(token, database_id, notion_version)
    data_sources = data.get("data_sources") or []
    if not isinstance(data_sources, list) or not data_sources:
        return None
    first = data_sources[0]
    if not isinstance(first, dict):
        return None
    ds_id = first.get("id")
    return ds_id if isinstance(ds_id, str) else None


def resolve_target_parent(
    token: str,
    notion_version: str,
    database_id: str | None,
    data_source_id: str | None,
) -> tuple[str | None, str | None]:
    db_id = database_id.strip() if isinstance(database_id, str) else ""
    ds_id = data_source_id.strip() if isinstance(data_source_id, str) else ""

    if db_id:
        database_metadata = fetch_database_metadata(token, db_id, notion_version)
        canonical_db_id = database_metadata.get("id") if isinstance(database_metadata.get("id"), str) else db_id
        candidate_data_sources = extract_data_source_ids(database_metadata)

        if ds_id and not any(same_notion_id(ds_id, candidate) for candidate in candidate_data_sources):
            raise ValueError(
                "指定した Notion 保存先が一致しません。"
                f" notion_database_id={db_id} に notion_data_source_id={ds_id} は紐づいていません"
            )

        if not ds_id:
            ds_id = candidate_data_sources[0] if candidate_data_sources else None

        return canonical_db_id, ds_id

    if ds_id:
        return None, ds_id

    raise ValueError("database_id または data_source_id が必要です")


def fetch_data_source_property_types(token: str, data_source_id: str, notion_version: str) -> dict[str, str]:
    headers = notion_headers(token, notion_version)
    data = notion_get(f"https://api.notion.com/v1/data_sources/{data_source_id}", headers)
    props = data.get("properties") or {}
    if not isinstance(props, dict):
        return {}
    out: dict[str, str] = {}
    for name, val in props.items():
        if isinstance(name, str) and isinstance(val, dict):
            t = val.get("type")
            if isinstance(t, str):
                out[name] = t
    return out


def split_rich_text(content: str, chunk_size: int = 1800) -> list[dict[str, Any]]:
    sanitized = sanitize_notion_text(content)
    if not sanitized:
        return [{"type": "text", "text": {"content": ""}}]
    
    parts = []
    # Match bold (**text**), markdown link ([text](url)), angle URL (<http...>), and raw URL (http...)
    pattern = r'(\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\)|<https?://[^>]+>|https?://[^\s<>()]+)'
    tokens = re.split(pattern, sanitized)
    
    for token in tokens:
        if not token:
            continue
            
        is_bold = token.startswith("**") and token.endswith("**")
        is_md_link = token.startswith("[") and "](" in token and token.endswith(")")
        is_angle_url = token.startswith("<http") and token.endswith(">")
        is_raw_url = token.startswith("http://") or token.startswith("https://")
        
        if is_bold:
            text_content = token[2:-2]
            for i in range(0, len(text_content), chunk_size):
                parts.append({
                    "type": "text",
                    "text": {"content": text_content[i:i+chunk_size]},
                    "annotations": {"bold": True}
                })
        elif is_md_link:
            m = re.match(r'\[([^\]]+)\]\(([^)]+)\)', token)
            if m:
                text_content = m.group(1)
                url = m.group(2)
                for i in range(0, len(text_content), chunk_size):
                    parts.append({
                        "type": "text",
                        "text": {
                            "content": text_content[i:i+chunk_size],
                            "link": {"url": url}
                        }
                    })
        elif is_angle_url:
            url = token[1:-1]
            for i in range(0, len(url), chunk_size):
                parts.append({
                    "type": "text",
                    "text": {
                        "content": url[i:i+chunk_size],
                        "link": {"url": url}
                    }
                })
        elif is_raw_url:
            for i in range(0, len(token), chunk_size):
                parts.append({
                    "type": "text",
                    "text": {
                        "content": token[i:i+chunk_size],
                        "link": {"url": token}
                    }
                })
        else:
            for i in range(0, len(token), chunk_size):
                parts.append({
                    "type": "text",
                    "text": {"content": token[i:i+chunk_size]}
                })
            
    return parts


def sanitize_notion_text(text: str | None) -> str:
    if not text:
        return ""
    cleaned = html.unescape(str(text))
    cleaned = BR_TAG_RE.sub("\n", cleaned)
    cleaned = HTML_TAG_RE.sub("", cleaned)
    # Preservation of asterisks for bold parsing later
    return cleaned


def parse_markdown_table(text: str) -> list[dict[str, Any]] | None:
    lines = text.strip().splitlines()
    if len(lines) < 2:
        return None

    # Check if first line and second line have pipes, indicating a table structure
    if "|" not in lines[0] or "|" not in lines[1]:
        return None

    # Check if second line is separator line (e.g. |---|---|)
    if not re.match(r"^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?$", lines[1].strip()):
        return None

    # Helper to split row by pipe, handling escaped pipes if necessary (simple implementation here)
    def parse_row(line: str) -> list[str]:
        # Remove leading/trailing pipes
        content = line.strip()
        if content.startswith("|"):
            content = content[1:]
        if content.endswith("|"):
            content = content[:-1]
        return [c.strip() for c in content.split("|")]

    headers = parse_row(lines[0])
    # Separator line is lines[1], skip it
    
    rows = []
    for line in lines[2:]:
        stripped = line.strip()
        if not stripped:
            break
        # A valid markdown table row must contain at least one pipe.
        if "|" not in stripped:
            break
        rows.append(parse_row(line))

    if not rows:
        return None

    # Ensure all rows have same number of cells as headers
    width = len(headers)
    table_rows = []

    # Header row
    table_rows.append({
        "type": "table_row",
        "table_row": {
            "cells": [split_rich_text(h) for h in headers]
        }
    })

    # Body rows
    for row in rows:
        # Pad or truncate row to match header width
        cells = row[:width] + [""] * (width - len(row))
        table_rows.append({
            "type": "table_row",
            "table_row": {
                "cells": [split_rich_text(c) for c in cells]
            }
        })

    return [{
        "object": "block",
        "type": "table",
        "table": {
            "table_width": width,
            "has_column_header": True,
            "has_row_header": False,
            "children": table_rows
        }
    }]


def parse_code_block(text: str) -> list[dict[str, Any]] | None:
    # Basic check for fenced code block
    m = re.match(r"^```(\w*)\n(.*)\n```$", text.strip(), re.DOTALL)
    if not m:
        return None
    
    lang = m.group(1).strip() or "plain text"
    code = m.group(2)
    
    # Notion supported languages map (simplified)
    # If lang is not supported, Notion might reject or default. 
    # For now, pass as is, or default to "plain text" if empty.
    
    return [{
        "object": "block",
        "type": "code",
        "code": {
            "caption": [],
            "rich_text": split_rich_text(code),
            "language": lang if lang else "plain text"
        }
    }]


def detect_title_property(available_types: dict[str, str], property_map: dict[str, str]) -> str | None:
    mapped = property_map.get("title")
    if mapped and available_types.get(mapped) == "title":
        return mapped
    for alias in CANONICAL_PROPERTY_ALIASES["title"]:
        if available_types.get(alias) == "title":
            return alias
    for name, t in available_types.items():
        if t == "title":
            return name
    return None


def add_property(props: dict[str, Any], name: str, notion_type: str, value: Any) -> None:
    if value is None:
        return
    if notion_type == "title":
        props[name] = {"title": split_rich_text(str(value))}
    elif notion_type == "rich_text":
        props[name] = {"rich_text": split_rich_text(str(value))}
    elif notion_type == "url":
        v = str(value).strip()
        if v:
            props[name] = {"url": v}
    elif notion_type == "date":
        v = str(value).strip()
        if v:
            props[name] = {"date": {"start": v}}
    elif notion_type == "checkbox":
        props[name] = {"checkbox": bool(value)}
    elif notion_type == "select":
        v = str(value).strip()
        if v:
            props[name] = {"select": {"name": v}}
    elif notion_type == "status":
        v = str(value).strip()
        if v:
            props[name] = {"status": {"name": v}}
    elif notion_type == "multi_select":
        if isinstance(value, list):
            values = [{"name": str(x)} for x in value if str(x).strip()]
        else:
            values = [{"name": str(value)}] if str(value).strip() else []
        if values:
            props[name] = {"multi_select": values}


def infer_mapped_property(canonical_key: str, available_types: dict[str, str], property_map: dict[str, str]) -> tuple[str, str] | None:
    mapped = property_map.get(canonical_key)
    if mapped and mapped in available_types:
        return mapped, available_types[mapped]
    for alias in CANONICAL_PROPERTY_ALIASES.get(canonical_key, []):
        if alias in available_types:
            return alias, available_types[alias]
    return None


def build_properties(pkg: dict[str, Any], available_types: dict[str, str], property_map: dict[str, str]) -> tuple[dict[str, Any], list[str]]:
    props: dict[str, Any] = {}
    skipped: list[str] = []

    title_prop = detect_title_property(available_types, property_map)
    if not title_prop:
        raise ValueError("Notionのtitleプロパティが見つかりません")
    add_property(props, title_prop, "title", pkg.get("title") or "投稿ドキュメント")

    field_values = {
        "theme": pkg.get("theme", ""),
        "workflow": pkg.get("workflow", ""),
        "status": pkg.get("status", "承認済み"),
        "approved": pkg.get("approved", False),
        "created_at": pkg.get("created_at", ""),
        "approved_at": pkg.get("approved_at", ""),
        "source_url": pkg.get("source_url", ""),
        "tags": pkg.get("tags", []),
    }

    for key, value in field_values.items():
        mapped = infer_mapped_property(key, available_types, property_map)
        if not mapped:
            skipped.append(f"{key}:missing")
            continue
        prop_name, prop_type = mapped
        add_property(props, prop_name, prop_type, value)

    return props, skipped


def text_to_blocks(text: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    lines = text.splitlines() if text else [""]
    buf = []
    in_code_block = False
    
    for line in lines:
        if line.strip().startswith("```"):
            if in_code_block:
                # End of code block
                buf.append(line)
                in_code_block = False
                # Flush code block
                code_text = "\n".join(buf)
                block = parse_code_block(code_text)
                if block:
                    blocks.extend(block)
                else:
                    # Fallback if parsing failed
                    blocks.extend(paragraph_blocks(code_text))
                buf = []
                continue
            else:
                # Start of code block -> Flush previous buffer first
                if buf:
                    blocks.extend(text_to_blocks_simple("\n".join(buf)))
                    buf = []
                in_code_block = True
                buf.append(line)
                continue

        if in_code_block:
            buf.append(line)
            continue

        # Normal text handling
        buf.append(line)

    if buf:
        # Flush remaining
        remaining_text = "\n".join(buf)
        if in_code_block:
             # Unclosed code block, treat as text
             blocks.extend(text_to_blocks_simple(remaining_text))
        else:
             blocks.extend(text_to_blocks_simple(remaining_text))
             
    if not blocks:
        blocks = paragraph_blocks("")
    return blocks


def text_to_blocks_simple(text: str) -> list[dict[str, Any]]:
    # 1. Try generic table parser
    table_block = parse_markdown_table(text)
    if table_block:
        return table_block

    # 2. Paragraphs & Headings
    blocks: list[dict[str, Any]] = []
    lines = text.splitlines()
    buf = []
    
    def flush():
        nonlocal buf
        if not buf:
            return
        paragraph = "\n".join(buf)
        # Check if this paragraph looks like a table
        table_block = parse_markdown_table(paragraph)
        if table_block:
            blocks.extend(table_block)
        else:
            # Rely on split_rich_text inline bold parsing
            blocks.extend(paragraph_blocks(paragraph))
        buf = []

    for line in lines:
        stripped = line.strip()
        
        # Check for H2: ## Heading
        m2 = re.match(r"^##\s+(.+)$", stripped)
        if m2:
            flush()
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": split_rich_text(m2.group(1).strip())}
            })
            continue

        # Check for H3: ### Heading or bold standalone line
        m3 = re.match(r"^###\s+(.+)$", stripped)
        m_bold = re.match(r"^(\*\*|__)(.+?)(\1)\s*$", stripped)
        
        if m3:
            flush()
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": split_rich_text(m3.group(1).strip())}
            })
            continue
        elif m_bold:
            flush()
            heading_text = m_bold.group(2).strip()
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": split_rich_text(heading_text)}
            })
            continue

        if not stripped:
            flush()
            continue
            
        buf.append(line)
        
    flush()
            
    return blocks
    if not blocks:
        blocks = paragraph_blocks("")
    return blocks


def paragraph_blocks(text: str, chunk_size: int = 1800) -> list[dict[str, Any]]:
    if not text:
        return [{"object": "block", "type": "paragraph", "paragraph": {"rich_text": split_rich_text("")}}]
    out = []
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i+chunk_size]
        out.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": split_rich_text(chunk)},
        })
    return out


def build_children(pkg: dict[str, Any]) -> list[dict[str, Any]]:
    sections = pkg.get("sections")
    if not isinstance(sections, dict):
        sections = {}
    children: list[dict[str, Any]] = []
    for key, label in SECTION_ORDER:
        body = str(sections.get(key, "")).strip()
        if not body:
            continue
        if label:
            children.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": split_rich_text(label)},
            })
        children.extend(text_to_blocks(body))
    return children


BLOCK_BATCH_SIZE = 100


def append_children(token: str, notion_version: str, page_id: str, children: list[dict[str, Any]]) -> None:
    """Append children blocks to an existing page in batches of BLOCK_BATCH_SIZE."""
    headers = notion_headers(token, notion_version)
    for i in range(0, len(children), BLOCK_BATCH_SIZE):
        batch = children[i:i + BLOCK_BATCH_SIZE]
        notion_request(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            "PATCH",
            headers,
            {"children": batch},
        )


def create_page(token: str, notion_version: str, database_id: str | None, data_source_id: str | None, properties: dict[str, Any], children: list[dict[str, Any]]) -> dict[str, Any]:
    headers = notion_headers(token, notion_version)
    if data_source_id:
        parent = {"type": "data_source_id", "data_source_id": data_source_id}
    elif database_id:
        parent = {"type": "database_id", "database_id": database_id}
    else:
        raise ValueError("database_id または data_source_id が必要です")

    first_batch = children[:BLOCK_BATCH_SIZE]
    remaining = children[BLOCK_BATCH_SIZE:]

    payload: dict[str, Any] = {
        "parent": parent,
        "properties": properties,
    }
    if first_batch:
        payload["children"] = first_batch

    result = notion_request("https://api.notion.com/v1/pages", "POST", headers, payload)

    # Append remaining blocks in batches if page was created successfully
    if remaining and result.get("id"):
        append_children(token, notion_version, result["id"], remaining)

    return result


def validate_package(pkg: dict[str, Any], force: bool) -> None:
    if not pkg.get("title"):
        raise ValueError("title が必要です")
    if "sections" not in pkg or not isinstance(pkg["sections"], dict):
        raise ValueError("sections オブジェクトが必要です")


def write_output(path: str | None, payload: dict[str, Any]) -> None:
    content = json.dumps(payload, ensure_ascii=False, indent=2)
    if path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
    else:
        print(content)


def main() -> int:
    args = parse_args()

    try:
        pkg = load_json(args.input)
        # dry-run should validate structure even before formal approval.
        validate_package(pkg, args.force or args.dry_run)

        if not pkg.get("created_at"):
            pkg["created_at"] = datetime.now(timezone.utc).date().isoformat()

        prop_map = load_property_map(args.property_map)
        resolved_parent = {
            "type": "data_source_id",
            "id": args.notion_data_source_id,
        } if args.notion_data_source_id else {
            "type": "database_id",
            "id": args.notion_database_id,
        }

        if args.dry_run:
            write_output(args.output, {
                "ok": True,
                "mode": "dry_run",
                "title": pkg.get("title"),
                "approved": bool(pkg.get("approved", False)),
                "sections": list((pkg.get("sections") or {}).keys()),
                "target_config": args.target_config,
                "notion_database_id": args.notion_database_id,
                "notion_data_source_id": args.notion_data_source_id,
                "resolved_parent": resolved_parent,
                "message": "Notion保存は実行していません",
            })
            return 0

        if not args.notion_token:
            raise ValueError("NOTION_API_KEY が未設定です")

        notion_database_id, data_source_id = resolve_target_parent(
            args.notion_token,
            args.notion_version,
            args.notion_database_id,
            args.notion_data_source_id,
        )

        available = {}
        if data_source_id:
            available = fetch_data_source_property_types(args.notion_token, data_source_id, args.notion_version)

        if not available:
            # fallback when schema fetch is unavailable: assume defaults
            available = {
                prop_map.get("title", "Name"): "title",
            }

        properties, skipped = build_properties(pkg, available, prop_map)
        children = build_children(pkg)
        notion_page = create_page(
            token=args.notion_token,
            notion_version=args.notion_version,
            database_id=notion_database_id,
            data_source_id=data_source_id,
            properties=properties,
            children=children,
        )

        write_output(args.output, {
            "ok": True,
            "status": "created",
            "title": pkg.get("title"),
            "skipped_properties": skipped,
            "page_id": notion_page.get("id"),
            "page_url": notion_page.get("url"),
            "notion_database_id": notion_database_id,
            "data_source_id": data_source_id,
            "resolved_parent": {
                "type": "data_source_id",
                "id": data_source_id,
            } if data_source_id else {
                "type": "database_id",
                "id": notion_database_id,
            },
            "target_config": args.target_config,
        })
        return 0
    except Exception as exc:
        write_output(args.output, {
            "ok": False,
            "error": str(exc),
        })
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
