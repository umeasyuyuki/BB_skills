#!/usr/bin/env python3
"""日本語フィード投稿向けのカテゴリと深掘り判定ルーター。"""

import argparse
import json


COMMAND_TO_WORKFLOW = {
    "/orchestrate-picks": "picks",
    "/orchestrate-myth": "myth",
    "/orchestrate-harms": "harms",
    "/orchestrate-intake": "intake",
    "/orchestrate-auto": "auto",
}
SAVE_RATE_THRESHOLD = 0.5


def calc_save_rate_pct(args):
    if args.save_rate_pct is not None:
        return args.save_rate_pct
    if args.saves is not None and args.views is not None and args.views > 0:
        return (args.saves / args.views) * 100
    return None


def decide_depth(args, save_rate_pct):
    if args.force_deep:
        return "deep", "forced"
    if args.force_standard:
        return "standard", "forced"
    if save_rate_pct is not None and save_rate_pct >= SAVE_RATE_THRESHOLD:
        return "deep", "save_rate_threshold"
    signals = [args.high_save_signal, args.mechanism_critical, args.trend_signal]
    if any(signals):
        return "deep", "qualitative_signal"
    return "standard", "default"


def main():
    parser = argparse.ArgumentParser(description="TikTok fitness workflow router")
    parser.add_argument("--command", choices=sorted(COMMAND_TO_WORKFLOW.keys()), required=True)
    parser.add_argument("--theme", required=True)
    parser.add_argument("--save-rate-pct", type=float)
    parser.add_argument("--saves", type=int)
    parser.add_argument("--views", type=int)
    parser.add_argument("--force-deep", action="store_true")
    parser.add_argument("--force-standard", action="store_true")
    parser.add_argument("--high-save-signal", action="store_true")
    parser.add_argument("--mechanism-critical", action="store_true")
    parser.add_argument("--trend-signal", action="store_true")
    args = parser.parse_args()

    save_rate_pct = calc_save_rate_pct(args)
    depth_mode, depth_reason = decide_depth(args, save_rate_pct)

    payload = {
        "command": args.command,
        "workflow": COMMAND_TO_WORKFLOW[args.command],
        "theme": args.theme,
        "depth_mode": depth_mode,
        "depth_reason": depth_reason,
        "save_rate_pct": round(save_rate_pct, 3) if save_rate_pct is not None else None,
        "save_rate_threshold_pct": SAVE_RATE_THRESHOLD,
        "profile": {
            "language": "ja",
            "kpi": "save_count_and_comments",
            "audience": "male_lifters_20_40_intermediate_plus",
            "readability": "high_school",
            "tone": "passionate_anger_fact_and_ideology",
            "slide_count": "10",
            "slide1_chars": "13-25",
            "slide2plus_chars": "30-50",
            "format": "markdown"
        },
        "outputs": [
            "台本",
            "素材管理表",
            "総まとめ表画像（1枚分の設計）",
            "根拠リンク",
            "薬機法・表現チェック結果"
        ]
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
