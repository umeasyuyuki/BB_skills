#!/usr/bin/env python3
"""
台本Markdownをパースして slides.json を生成する。

既存の tiktok-fit-carousel-script の出力フォーマットに対応:
- ## N枚目（...）形式のスライド見出し
- スライド本文 → テロップ + ナレーション
- Markdown テーブル → tableData

Usage:
    python3 parse_script.py <script.md> [--output slides.json]
"""

import argparse
import json
import re
import sys
from pathlib import Path


def parse_slide_heading(line: str) -> dict | None:
    """## 1枚目（結論フック） or ## スライド1 形式をパース"""
    patterns = [
        r"^##\s*(\d+)枚目[（(](.+?)[）)]",
        r"^##\s*スライド\s*(\d+)",
        r"^##\s*(\d+)枚目",
    ]
    for pat in patterns:
        m = re.match(pat, line.strip())
        if m:
            idx = int(m.group(1)) - 1
            label = m.group(2) if m.lastindex >= 2 else ""
            return {"index": idx, "label": label}
    return None


def detect_slide_type(index: int, total: int, label: str, text: str) -> str:
    """スライドタイプを自動判定"""
    label_lower = label.lower()

    if index == 0 or "フック" in label or "サムネ" in label:
        return "hook"
    if "まとめ" in label or "総まとめ" in text:
        return "table"
    if index >= total - 1 or "CTA" in label or "保存" in label or "コメント" in label:
        return "cta"
    return "content"


def parse_markdown_table(lines: list[str]) -> tuple[list[str], list[dict]]:
    """Markdownテーブルをパースして columns, rows を返す"""
    columns: list[str] = []
    rows: list[dict] = []
    table_started = False

    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            if table_started:
                break
            continue

        cells = [c.strip() for c in line.split("|")[1:-1]]

        if not columns:
            columns = cells
            table_started = True
            continue

        # Skip separator row (|---|---|)
        if all(re.match(r"^[-:]+$", c) for c in cells):
            continue

        row = {}
        for i, col in enumerate(columns):
            row[col] = cells[i] if i < len(cells) else ""
        rows.append(row)

    return columns, rows


def extract_narration(text: str) -> str:
    """スライドテキストからナレーション文を抽出。
    箇条書き・記号を自然な読み上げ文に変換する。"""
    lines = text.strip().split("\n")
    narration_parts = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # テーブル行はスキップ
        if line.startswith("|"):
            continue
        # 箇条書きマーカー除去
        line = re.sub(r"^[-*•]\s*", "", line)
        # 記号類の読み上げ変換
        line = line.replace("×", "バツ、").replace("○", "マル、").replace("◎", "二重マル、")
        line = line.replace("→", "、").replace("＋", "プラス")
        # 強調マーカー除去
        line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
        narration_parts.append(line)

    return "".join(narration_parts)


def extract_telop(text: str, max_chars: int = 30) -> str:
    """スライドテキストから短いテロップ文を抽出"""
    lines = text.strip().split("\n")
    # 最初の非空行を使う
    for line in lines:
        line = line.strip()
        if line and not line.startswith("|") and not re.match(r"^[-:]+$", line):
            # 強調マーカー除去
            line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
            # 長すぎる場合は切る
            if len(line) > max_chars:
                line = line[:max_chars - 1] + "…"
            return line
    return ""


def parse_script(md_text: str) -> list[dict]:
    """台本Markdownからスライドリストを生成"""
    lines = md_text.split("\n")
    slides_raw: list[dict] = []
    current_slide = None
    current_lines: list[str] = []

    # 台本セクションを検出
    in_script_section = False
    for line in lines:
        if re.match(r"^#\s*台本", line) or re.match(r"^##\s*\d+枚目", line):
            in_script_section = True
        if in_script_section and re.match(r"^#\s*キャプション", line):
            break

        if not in_script_section:
            continue

        heading = parse_slide_heading(line)
        if heading:
            if current_slide is not None:
                current_slide["text"] = "\n".join(current_lines)
                slides_raw.append(current_slide)
            current_slide = heading
            current_lines = []
        elif current_slide is not None:
            current_lines.append(line)

    # Last slide
    if current_slide is not None:
        current_slide["text"] = "\n".join(current_lines)
        slides_raw.append(current_slide)

    # Convert to SlideData format
    total = len(slides_raw)
    slides = []
    for raw in slides_raw:
        text = raw["text"]
        slide_type = detect_slide_type(raw["index"], total, raw.get("label", ""), text)

        slide: dict = {
            "index": raw["index"],
            "telop": extract_telop(text),
            "narration": extract_narration(text),
            "durationInFrames": 150,  # placeholder, calculated from audio
            "slideType": slide_type,
        }

        # テーブルスライドの場合、テーブルデータをパース
        if slide_type == "table" or "|" in text:
            table_lines = text.split("\n")
            columns, table_data = parse_markdown_table(table_lines)
            if columns and table_data:
                slide["slideType"] = "table"
                slide["tableColumns"] = columns
                slide["tableData"] = table_data

        slides.append(slide)

    return slides


def main():
    parser = argparse.ArgumentParser(description="Parse carousel script to slides JSON")
    parser.add_argument("input", help="Path to script markdown file")
    parser.add_argument("--output", "-o", default="slides.json", help="Output JSON path")
    parser.add_argument("--workflow", "-w", default="auto", help="Workflow type")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    md_text = input_path.read_text(encoding="utf-8")
    slides = parse_script(md_text)

    if not slides:
        print("Warning: No slides found in script", file=sys.stderr)
        sys.exit(1)

    output = {
        "title": input_path.stem,
        "workflow": args.workflow,
        "transitionDurationFrames": 15,
        "bgStyle": "gradient",
        "slides": slides,
    }

    output_path = Path(args.output)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Parsed {len(slides)} slides → {output_path}")


if __name__ == "__main__":
    main()
