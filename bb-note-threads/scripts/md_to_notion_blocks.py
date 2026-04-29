#!/usr/bin/env python3
"""md_to_notion_blocks.py — Markdown → Notion blocks JSON 変換.

bb-note-threads の Note 出力 markdown を Notion API の children 配列に変換する。
note.com コピペ最適化（A 案）に従い、段落・見出し・箇条書き・太字を保持する。

サポート要素:
- # H1: skip（Notion ページの title プロパティに使うため）
- ## H2: heading_2（note.com の大見出し）
- ### H3: heading_3（note.com の中見出し）
- 通常段落: paragraph
- - リスト: bulleted_list_item
- > 引用: quote
- ────────（U+2500 連続）または ---: divider
- **太字**: rich_text annotations.bold = true

設計方針:
- writer は各論理段落を 1 行で出力する規約。本スクリプトはその前提で動作する。
- 同一段落内の物理改行（\\n）は空白結合せず、空文字列で結合（日本語前提）。
- bold 以外のインライン装飾（イタリック、リンク、コード）は今回サポート外。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from typing import List, Dict, Any

BOLD_PATTERN = re.compile(r"\*\*(.+?)\*\*")
DIVIDER_PATTERNS = ("─" * 4, "---")
RICH_TEXT_SEGMENT_LIMIT = 1900  # Notion API は 2000 char 上限、安全マージンあり


def parse_rich_text(text: str) -> List[Dict[str, Any]]:
    """Markdown の **bold** を Notion rich_text 配列に変換する。"""
    if not text:
        return [{"type": "text", "text": {"content": ""}}]

    segments: List[Dict[str, Any]] = []
    cursor = 0
    for match in BOLD_PATTERN.finditer(text):
        if match.start() > cursor:
            plain = text[cursor:match.start()]
            segments.extend(_split_long_text(plain, bold=False))
        bold_inner = match.group(1)
        segments.extend(_split_long_text(bold_inner, bold=True))
        cursor = match.end()
    if cursor < len(text):
        segments.extend(_split_long_text(text[cursor:], bold=False))

    if not segments:
        segments.append({"type": "text", "text": {"content": text}})
    return segments


def _split_long_text(text: str, *, bold: bool) -> List[Dict[str, Any]]:
    """1 segment が Notion の rich_text 上限を超える場合は分割する。"""
    if not text:
        return []
    chunks = [
        text[i:i + RICH_TEXT_SEGMENT_LIMIT]
        for i in range(0, len(text), RICH_TEXT_SEGMENT_LIMIT)
    ]
    out: List[Dict[str, Any]] = []
    for chunk in chunks:
        seg: Dict[str, Any] = {
            "type": "text",
            "text": {"content": chunk},
        }
        if bold:
            seg["annotations"] = {"bold": True}
        out.append(seg)
    return out


def _is_divider(line: str) -> bool:
    stripped = line.strip()
    if stripped == "---":
        return True
    return bool(stripped) and all(ch == "─" for ch in stripped) and len(stripped) >= 4


def md_to_blocks(md_text: str, *, skip_h1: bool = True) -> List[Dict[str, Any]]:
    """Markdown 全文を Notion blocks 配列に変換する。"""
    lines = md_text.split("\n")
    blocks: List[Dict[str, Any]] = []
    para_buf: List[str] = []
    quote_buf: List[str] = []

    def flush_para() -> None:
        if not para_buf:
            return
        # 同一段落内の物理改行を空文字列で結合（日本語前提）
        text = "".join(para_buf).strip()
        para_buf.clear()
        if not text:
            return
        blocks.append({
            "type": "paragraph",
            "paragraph": {"rich_text": parse_rich_text(text)},
        })

    def flush_quote() -> None:
        if not quote_buf:
            return
        text = "".join(quote_buf).strip()
        quote_buf.clear()
        if not text:
            return
        blocks.append({
            "type": "quote",
            "quote": {"rich_text": parse_rich_text(text)},
        })

    for raw in lines:
        line = raw.rstrip()

        if line.startswith("# ") and skip_h1:
            flush_para()
            flush_quote()
            continue
        if line.startswith("### "):
            flush_para()
            flush_quote()
            blocks.append({
                "type": "heading_3",
                "heading_3": {"rich_text": parse_rich_text(line[4:])},
            })
        elif line.startswith("## "):
            flush_para()
            flush_quote()
            blocks.append({
                "type": "heading_2",
                "heading_2": {"rich_text": parse_rich_text(line[3:])},
            })
        elif line.startswith("# "):
            # H1 を本文に含める（--include-h1）場合は H2 として降格
            flush_para()
            flush_quote()
            blocks.append({
                "type": "heading_2",
                "heading_2": {"rich_text": parse_rich_text(line[2:])},
            })
        elif line.startswith("- "):
            flush_para()
            flush_quote()
            blocks.append({
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": parse_rich_text(line[2:])},
            })
        elif line.startswith("> "):
            flush_para()
            quote_buf.append(line[2:])
        elif _is_divider(line):
            flush_para()
            flush_quote()
            blocks.append({"type": "divider", "divider": {}})
        elif line == "":
            flush_para()
            flush_quote()
        else:
            if quote_buf:
                quote_buf.append(line)
            else:
                para_buf.append(line)

    flush_para()
    flush_quote()
    return blocks


def main() -> int:
    ap = argparse.ArgumentParser(
        description="bb-note-threads: Note markdown を Notion blocks JSON に変換する。"
    )
    ap.add_argument("input", help="入力 Markdown ファイルパス")
    ap.add_argument(
        "--include-h1",
        action="store_true",
        help="H1 を本文に含める（既定では title プロパティに使うため除外）",
    )
    ap.add_argument(
        "--cutoff-marker",
        default=None,
        help="このマーカー以降を切り捨てる（メタデータ・セルフチェック結果除外用、例: '---'）",
    )
    ap.add_argument(
        "--cutoff-after-section",
        default=None,
        help="この見出し以降の最初の cutoff-marker で切り捨てる（例: '## 脚注'）",
    )
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as f:
        md = f.read()

    if args.cutoff_after_section and args.cutoff_marker:
        section_idx = md.find(args.cutoff_after_section)
        if section_idx >= 0:
            tail = md[section_idx:]
            sep_idx = tail.find(args.cutoff_marker, len(args.cutoff_after_section))
            if sep_idx >= 0:
                md = md[: section_idx + sep_idx]
    elif args.cutoff_marker:
        sep_idx = md.rfind(args.cutoff_marker)
        if sep_idx >= 0:
            md = md[:sep_idx]

    blocks = md_to_blocks(md, skip_h1=not args.include_h1)
    json.dump(blocks, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
