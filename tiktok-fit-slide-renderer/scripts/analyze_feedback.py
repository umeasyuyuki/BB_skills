#!/usr/bin/env python3
"""
analyze_feedback.py - フィードバックログからパターンを検出し、ルール昇格を提案する

Usage:
    python3 analyze_feedback.py
    python3 analyze_feedback.py --threshold 3  # 検出しきい値
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
FEEDBACK_LOG = SKILL_DIR / "data" / "pipeline" / "feedback_log.jsonl"


def load_entries() -> list[dict]:
    if not FEEDBACK_LOG.exists():
        return []
    entries = []
    with FEEDBACK_LOG.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def analyze(entries: list[dict], threshold: int) -> list[dict]:
    """パターンを検出して提案リストを返す"""
    # field単位でカウント
    field_counter = Counter()
    field_changes = defaultdict(list)

    for e in entries:
        field = e.get("field", "")
        before = e.get("before")
        after = e.get("after")
        if not field:
            continue
        field_counter[field] += 1
        field_changes[field].append({
            "before": before,
            "after": after,
            "slide": e.get("slide"),
            "reason": e.get("reason", ""),
        })

    suggestions = []
    for field, count in field_counter.most_common():
        if count < threshold:
            continue

        changes = field_changes[field]
        # after値の最頻出値を求める
        after_values = [c["after"] for c in changes if c["after"] is not None]
        after_counter = Counter(str(v) for v in after_values)
        most_common_after, most_common_count = after_counter.most_common(1)[0] if after_counter else (None, 0)

        priority = "HIGH" if count >= threshold * 2 else "MED" if count >= threshold else "LOW"
        suggestions.append({
            "priority": priority,
            "field": field,
            "count": count,
            "most_common_after": most_common_after,
            "most_common_count": most_common_count,
            "samples": changes[:3],
        })

    return suggestions


def print_suggestions(suggestions: list[dict]):
    if not suggestions:
        print("パターンは検出されませんでした（ログが少ないか、バラバラな修正）")
        return

    print("─" * 60)
    print(f"パターン検出結果（{sum(s['count'] for s in suggestions)}件の調整）")
    print("─" * 60)

    for s in suggestions:
        print()
        print(f"[{s['priority']}] {s['field']} が {s['count']} 回発生")
        if s["most_common_after"] and s["most_common_count"] >= 2:
            print(f"  → 最頻値: {s['most_common_after']} ({s['most_common_count']}回)")
        print(f"  サンプル:")
        for sample in s["samples"]:
            print(
                f"    slide={sample.get('slide')}, "
                f"{sample['before']} → {sample['after']}, "
                f"reason={sample.get('reason', '')[:30]}"
            )
    print()
    print("─" * 60)
    print("→ これらをルール（style_config.json）に反映することを推奨します")
    print("─" * 60)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--threshold", type=int, default=3, help="検出のしきい値（デフォルト3）")
    args = p.parse_args()

    entries = load_entries()
    print(f"\nフィードバックログ: {len(entries)}件")

    if not entries:
        print("ログが空です。--render 実行時の調整が記録されていません。")
        return 0

    suggestions = analyze(entries, args.threshold)
    print_suggestions(suggestions)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
