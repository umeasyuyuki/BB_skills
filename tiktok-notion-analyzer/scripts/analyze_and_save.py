#!/usr/bin/env python3
"""Analyze TikTok post performance and optionally save the result to Notion."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_PROPERTY_MAP = {
    "title": "Name",
    "post_id": "Post ID",
    "url": "Post URL",
    "published_at": "Published At",
    "views": "Views",
    "likes": "Likes",
    "comments": "Comments",
    "saves": "Saves",
    "engagement_rate": "Engagement Rate",
    "like_rate": "Like Rate",
    "comment_rate": "Comment Rate",
    "save_rate": "Save Rate",
    "content_summary": "Content Summary",
    "why_engagement": "Why Engagement",
    "save_improvements": "Save Improvements",
    "analysis_markdown": "Analysis",
}

CANONICAL_PROPERTY_ALIASES = {
    "title": ["Name", "名前", "投稿のテーマ名", "Title"],
    "post_id": ["Post ID", "投稿ID", "投稿ID（TikTok）"],
    "url": ["Post URL", "投稿URL", "投稿のリンク", "URL"],
    "published_at": ["Published At", "投稿日", "投稿の作成日"],
    "views": ["Views", "再生数", "再生回数"],
    "likes": ["Likes", "いいね数"],
    "comments": ["Comments", "コメント数"],
    "saves": ["Saves", "保存数"],
    "engagement_rate": ["Engagement Rate", "エンゲージメント率"],
    "like_rate": ["Like Rate", "いいね率"],
    "comment_rate": ["Comment Rate", "コメント率"],
    "save_rate": ["Save Rate", "保存率"],
    "content_summary": ["Content Summary", "内容要約", "テキスト"],
    "why_engagement": ["Why Engagement", "分析理由"],
    "save_improvements": ["Save Improvements", "改善案"],
    "analysis_markdown": ["Analysis", "分析", "テキスト"],
}

KPI_TARGETS = {
    "save_rate": 2.5,
    "swipe_completion_rate": 30.0,
    "search_traffic_rate": 20.0,
    "profile_visit_rate": 3.0,
    "follow_conversion_rate": 1.5,
}

PILLAR_KEYWORDS = {
    "fat_loss": [
        "fat loss",
        "脂肪",
        "減量",
        "体脂肪",
        "カロリー",
        "β酸化",
        "beta oxidation",
        "代謝",
    ],
    "hypertrophy": [
        "hypertrophy",
        "筋肥大",
        "mtor",
        "筋タンパク",
        "アミノ酸",
        "ロイシン",
        "タンパク質",
    ],
    "power": [
        "power",
        "筋出力",
        "big3",
        "神経",
        "アセチルコリン",
        "高重量",
        "パフォーマンス",
    ],
}

PILLAR_LABELS_JA = {
    "fat_loss": "脂肪燃焼",
    "hypertrophy": "筋肥大",
    "power": "筋出力",
    "unknown": "判定不能",
}

LEGAL_RISK_KEYWORDS = [
    "絶対",
    "100%",
    "必ず",
    "治る",
    "副作用なし",
    "完全保証",
]

NOISE_KEYWORDS = [
    "恋愛",
    "エンタメ",
    "vlog",
    "ガジェットレビュー",
    "旅行",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze TikTok metrics and optionally push results to Notion."
    )
    parser.add_argument("--input", help="Path to input JSON file")
    parser.add_argument("--url", help="TikTok post URL (alternative to --input)")
    parser.add_argument("--caption", help="Optional caption override when using --url")
    parser.add_argument(
        "--content-summary",
        help="Optional content summary override when using --url",
    )
    parser.add_argument("--hook", help="Optional hook text when using --url")
    parser.add_argument("--cta", help="Optional CTA text when using --url")
    parser.add_argument("--views", type=int, help="Views count")
    parser.add_argument("--likes", type=int, help="Likes count")
    parser.add_argument("--comments", type=int, help="Comments count")
    parser.add_argument("--saves", type=int, help="Saves count")
    parser.add_argument(
        "--allow-missing-metrics",
        action="store_true",
        help="Allow qualitative analysis when metrics are incomplete.",
    )
    parser.add_argument(
        "--output",
        help="Optional path to write output JSON. If omitted, print to stdout.",
    )
    parser.add_argument(
        "--property-map",
        help="Optional JSON file mapping canonical keys to Notion property names.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run analysis without writing to Notion.",
    )
    parser.add_argument(
        "--notion-token",
        default=os.getenv("NOTION_API_KEY"),
        help="Notion integration token. Defaults to NOTION_API_KEY env var.",
    )
    parser.add_argument(
        "--notion-database-id",
        default=os.getenv("NOTION_DATABASE_ID"),
        help="Notion database ID. Defaults to NOTION_DATABASE_ID env var.",
    )
    parser.add_argument(
        "--notion-data-source-id",
        default=os.getenv("NOTION_DATA_SOURCE_ID"),
        help="Notion data source ID. Preferred on API version 2025-09-03+.",
    )
    parser.add_argument(
        "--notion-version",
        default="2025-09-03",
        help="Notion-Version header value.",
    )
    return parser.parse_args()


def load_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Input JSON must be an object.")
    return data


def fetch_tiktok_oembed(url: str) -> dict[str, Any]:
    endpoint = "https://www.tiktok.com/oembed?url=" + urllib.parse.quote(url, safe="")
    request = urllib.request.Request(endpoint, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"TikTok oEmbed error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Failed to fetch TikTok oEmbed: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Unexpected TikTok oEmbed response format.")
    return payload


def extract_post_id_from_url(url: str) -> str:
    match = re.search(r"/video/(\d+)", url)
    return match.group(1) if match else ""


def build_payload_from_url(args: argparse.Namespace) -> dict[str, Any]:
    if not args.url:
        raise ValueError("--url is required for URL mode.")
    oembed = fetch_tiktok_oembed(args.url)
    title = str(oembed.get("title", "")).strip()
    caption = args.caption or title
    content_summary = args.content_summary or caption
    post = {
        "post_id": extract_post_id_from_url(args.url),
        "url": args.url,
        "caption": caption,
        "content_summary": content_summary,
        "hook": args.hook or "",
        "cta": args.cta or "",
        "hashtags": sorted(set(re.findall(r"#\w+", caption))),
    }
    metrics: dict[str, Any] = {}
    for key, value in [
        ("views", args.views),
        ("likes", args.likes),
        ("comments", args.comments),
        ("saves", args.saves),
    ]:
        if value is not None:
            metrics[key] = value
    return {"post": post, "metrics": metrics}


def as_int(value: Any, field_name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid integer for '{field_name}': {value!r}") from exc


def pct(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return (numerator / denominator) * 100.0


def join_lines(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def split_rich_text(content: str, chunk_size: int = 1900) -> list[dict[str, Any]]:
    if not content:
        return [{"type": "text", "text": {"content": ""}}]
    chunks: list[dict[str, Any]] = []
    for i in range(0, len(content), chunk_size):
        chunks.append({"type": "text", "text": {"content": content[i : i + chunk_size]}})
    return chunks


def load_property_map(path: str | None) -> dict[str, str]:
    if not path:
        return dict(DEFAULT_PROPERTY_MAP)
    data = load_json(path)
    if not all(isinstance(k, str) and isinstance(v, str) for k, v in data.items()):
        raise ValueError("Property map must be an object with string keys and values.")
    merged = dict(DEFAULT_PROPERTY_MAP)
    merged.update(data)
    return merged


def extract_post(payload: dict[str, Any]) -> dict[str, Any]:
    post: dict[str, Any] = {}
    post_section = payload.get("post")
    if isinstance(post_section, dict):
        post.update(post_section)
    for key in [
        "post_id",
        "url",
        "published_at",
        "caption",
        "content_summary",
        "hook",
        "cta",
        "hashtags",
    ]:
        if key in payload and key not in post:
            post[key] = payload[key]
    if not post.get("content_summary"):
        post["content_summary"] = post.get("caption", "")
    return post


def extract_metrics(payload: dict[str, Any], strict: bool = True) -> tuple[dict[str, int], list[str]]:
    metrics: dict[str, Any] = {}
    metrics_section = payload.get("metrics")
    if isinstance(metrics_section, dict):
        metrics.update(metrics_section)
    for key in ["views", "likes", "comments", "saves"]:
        if key in payload and key not in metrics:
            metrics[key] = payload[key]
    required = ["views", "likes", "comments", "saves"]
    missing = [key for key in required if key not in metrics]
    if missing and strict:
        raise ValueError(f"Missing required metric(s): {', '.join(missing)}")
    normalized: dict[str, int] = {}
    for key in required:
        if key in metrics:
            normalized[key] = as_int(metrics[key], key)
        else:
            normalized[key] = 0
    return normalized, missing


def extract_optional_metrics(payload: dict[str, Any]) -> dict[str, float]:
    optional_keys = [
        "swipe_completion_rate",
        "search_traffic_rate",
        "profile_visit_rate",
        "follow_conversion_rate",
        "profile_to_follow_rate",
    ]
    optional: dict[str, Any] = {}
    metrics_section = payload.get("metrics")
    if isinstance(metrics_section, dict):
        for key in optional_keys:
            if key in metrics_section:
                optional[key] = metrics_section[key]
    for key in optional_keys:
        if key in payload and key not in optional:
            optional[key] = payload[key]

    out: dict[str, float] = {}
    for key, value in optional.items():
        try:
            out[key] = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid number for '{key}': {value!r}") from exc
    return out


def collect_text(post: dict[str, Any]) -> str:
    return " ".join(
        str(post.get(key, ""))
        for key in ["caption", "content_summary", "hook", "cta"]
    ).lower()


def detect_primary_pillar(text: str) -> tuple[str, float, dict[str, int]]:
    scores: dict[str, int] = {}
    for pillar, keywords in PILLAR_KEYWORDS.items():
        scores[pillar] = sum(1 for keyword in keywords if keyword in text)
    best_pillar = max(scores, key=scores.get)
    best_score = scores[best_pillar]
    total = sum(scores.values())
    confidence = 0.0 if total == 0 else best_score / total
    if best_score == 0:
        return "unknown", 0.0, scores
    return best_pillar, confidence, scores


def evaluate_kpis(
    metrics: dict[str, float], optional_metrics: dict[str, float], missing_metrics: list[str]
) -> dict[str, Any]:
    current: dict[str, float] = {}
    if "saves" not in missing_metrics and "views" not in missing_metrics:
        current["save_rate"] = round(float(metrics.get("save_rate", 0.0)), 4)
    current.update(
        {
            key: round(float(value), 4)
            for key, value in optional_metrics.items()
            if key in KPI_TARGETS
        }
    )
    status: list[dict[str, Any]] = []
    for key, target in KPI_TARGETS.items():
        if key not in current:
            status.append({"kpi": key, "target": target, "current": None, "status": "欠損"})
            continue
        value = float(current[key])
        status.append(
            {
                "kpi": key,
                "target": target,
                "current": value,
                "status": "達成" if value >= target else "未達",
            }
        )
    met = sum(1 for row in status if row["status"] == "達成")
    observed = sum(1 for row in status if row["status"] != "欠損")
    return {
        "targets": KPI_TARGETS,
        "current": current,
        "status": status,
        "met_count": met,
        "observed_count": observed,
    }


def build_strategy_alignment(
    post: dict[str, Any],
    metrics: dict[str, float],
    optional_metrics: dict[str, float],
    missing_metrics: list[str],
    signals: dict[str, bool],
) -> dict[str, Any]:
    text = collect_text(post)
    pillar, confidence, pillar_scores = detect_primary_pillar(text)
    kpi_eval = evaluate_kpis(metrics, optional_metrics, missing_metrics)

    guardrail_flags: list[str] = []
    if pillar == "unknown":
        guardrail_flags.append(
            "3本柱との一致が弱いです。脂肪燃焼・筋肥大・筋出力のいずれかに明確に寄せてください。"
        )
    if any(keyword in text for keyword in NOISE_KEYWORDS):
        guardrail_flags.append("ノイズ混入リスク: 3本柱以外の話題が含まれています。")
    risky_terms = [term for term in LEGAL_RISK_KEYWORDS if term.lower() in text]
    if risky_terms:
        guardrail_flags.append(
            "法令リスク: 断定的または誤認を招く表現の可能性があります。"
        )
    if not signals.get("has_hook"):
        guardrail_flags.append("構成リスク: 1枚目の損失回避フックが弱い可能性があります。")
    if not signals.get("has_save_cta"):
        guardrail_flags.append("転換リスク: 保存を促すCTAが不足しています。")

    mission_score = 100
    if pillar == "unknown":
        mission_score -= 35
    if risky_terms:
        mission_score -= 25
    below_core_kpi = next(
        (row for row in kpi_eval["status"] if row["kpi"] == "save_rate" and row["status"] == "未達"),
        None,
    )
    if below_core_kpi:
        mission_score -= 20
    mission_score -= min(len(guardrail_flags) * 5, 20)
    mission_score = max(0, min(100, mission_score))

    return {
        "persona": {
            "age": 30,
            "gender": "male",
            "training_experience": "2-3 years",
            "goal": "初大会出場とBig3向上を、限られた時間で科学的に達成する",
        },
        "detected_pillar": pillar,
        "detected_pillar_ja": PILLAR_LABELS_JA.get(pillar, "判定不能"),
        "pillar_confidence": round(confidence, 4),
        "pillar_scores": pillar_scores,
        "kpi_evaluation": kpi_eval,
        "guardrail_flags": guardrail_flags,
        "legal_risk_terms": risky_terms,
        "mission_fit_score": mission_score,
    }


def detect_content_signals(post: dict[str, Any]) -> dict[str, bool]:
    text = " ".join(
        str(post.get(key, ""))
        for key in ["caption", "content_summary", "hook", "cta"]
    ).lower()
    has_step_keyword = any(token in text for token in ["step", "checklist", "framework"])
    has_numbered_steps = has_step_keyword or bool(
        re.search(r"(^|\n)\s*(\d+[\.\):]|[-*])\s+\w+", str(post.get("content_summary", "")))
        or re.search(r"(^|\n)\s*(\d+[\.\):]|[-*])\s+\w+", str(post.get("caption", "")))
    )
    has_numbers = bool(re.search(r"\d+", text))
    has_save_cta = any(
        token in text
        for token in ["save", "bookmark", "keep this", "保存", "見返", "あとで見る"]
    )
    has_comment_cta = any(
        token in text
        for token in ["comment", "reply", "tell me", "コメント", "教えて", "感想"]
    )
    has_hook = len(str(post.get("hook", "")).strip()) >= 8
    return {
        "has_numbered_steps": has_numbered_steps,
        "has_numbers": has_numbers,
        "has_save_cta": has_save_cta,
        "has_comment_cta": has_comment_cta,
        "has_hook": has_hook,
    }


def classify_rate(value: float, low: float, high: float) -> str:
    if value < low:
        return "low"
    if value >= high:
        return "high"
    return "mid"


def build_why_engagement(
    post: dict[str, Any], metrics: dict[str, float], signals: dict[str, bool]
) -> list[str]:
    views = metrics["views"]
    engagement_rate = metrics["engagement_rate"]
    like_rate = metrics["like_rate"]
    comment_rate = metrics["comment_rate"]
    save_rate = metrics["save_rate"]

    reasons: list[str] = []

    save_band = classify_rate(save_rate, low=0.35, high=0.9)
    if save_band == "low":
        reasons.append(
            "保存率が基準を下回っており、見て終わる投稿になっている可能性が高いです。"
        )
    elif save_band == "high":
        reasons.append(
            "保存率が高く、見返し価値のある資産コンテンツとして機能しています。"
        )
    else:
        reasons.append(
            "保存率は中位で、有用性は伝わるものの「必ず保存する価値」までは届いていません。"
        )

    if like_rate >= 4.0 and save_rate < 0.35:
        reasons.append(
            "いいね率に対して保存率が低く、共感は取れているが再利用価値の訴求が弱い状態です。"
        )
    if comment_rate >= 0.45:
        reasons.append(
            "コメント率が高く、受け身視聴よりも議論を誘発するテーマとして機能しています。"
        )
    if views >= 50000 and engagement_rate < 3.0:
        reasons.append(
            "到達は取れている一方で行動転換が弱く、フックから実利提示までの接続が不足しています。"
        )
    if views < 5000 and engagement_rate >= 5.0:
        reasons.append(
            "反応品質は高いため、課題は内容よりもパッケージと配信面にある可能性が高いです。"
        )

    if not signals["has_hook"]:
        reasons.append(
            "冒頭フックが弱く、最初の離脱を止める力が不足しています。"
        )
    if not signals["has_numbered_steps"]:
        reasons.append(
            "手順やチェックリスト構造が弱く、保存動機につながりにくい構成です。"
        )
    if not signals["has_numbers"]:
        reasons.append(
            "数値・閾値・具体条件が不足し、実務で使える情報としての説得力が落ちています。"
        )
    if signals["has_comment_cta"] and not signals["has_save_cta"]:
        reasons.append(
            "CTAがコメント寄りで、保存行動への導線が弱くなっています。"
        )

    if not reasons:
        reasons.append(
            "現状は大きな欠点はなく、今後はニッチの絞り込みと保存導線の強化で伸ばせます。"
        )
    return reasons[:6]


def build_save_improvements(
    metrics: dict[str, float], signals: dict[str, bool], post: dict[str, Any]
) -> list[str]:
    save_rate = metrics["save_rate"]
    views = metrics["views"]
    actions: list[str] = []

    if save_rate < 0.35:
        actions.append(
            "投稿を再利用可能な型（3ステップ/チェックリスト）に再設計し、各要点を明示してください。"
        )
    else:
        actions.append(
            "現行の価値提案を維持しつつ、すぐ実践できる具体手順を1つ追加してください。"
        )

    if not signals["has_save_cta"]:
        actions.append(
            "保存CTAを2回入れてください（核心提示直後と締め）。"
        )
    else:
        actions.append(
            "保存CTAを成果ベースにしてください（保存すると何が解決するかを明示）。"
        )

    if not signals["has_numbers"]:
        actions.append(
            "信頼性向上のため、具体的な数値・閾値・Before/After目標を追加してください。"
        )

    if not signals["has_numbered_steps"]:
        actions.append(
            "スライド構成を番号付き手順にして、見返しやすい設計にしてください。"
        )

    if views >= 50000 and save_rate < 0.35:
        actions.append(
            "表紙をベネフィット軸と成果軸でA/Bテストし、再生数ではなく保存率で最適化してください。"
        )
    elif views < 5000:
        actions.append(
            "内容は維持し、表紙・タイトル・1枚目だけ複数パターンを回して配信効率を上げてください。"
        )

    actions.append(
        "固定コメントに要点の再掲と保存促進の一文を入れてください。"
    )

    hashtag_count = len(post.get("hashtags", [])) if isinstance(post.get("hashtags"), list) else 0
    if hashtag_count == 0:
        actions.append(
            "保存意図の高い層に届くよう、意図一致ハッシュタグを少数精鋭で追加してください。"
        )

    return actions[:6]


def build_summary(metrics: dict[str, float]) -> str:
    save_rate = metrics["save_rate"]
    engagement_rate = metrics["engagement_rate"]
    if save_rate < 0.35:
        return (
            f"現在は即時反応型のエンゲージメントが中心です "
            f"(エンゲージメント率={engagement_rate:.2f}%, 保存率={save_rate:.2f}%)。"
        )
    if save_rate >= 0.9:
        return (
            f"投稿は見返し価値の高い資産として機能しています "
            f"(エンゲージメント率={engagement_rate:.2f}%, 保存率={save_rate:.2f}%)。"
        )
    return (
        f"有用性はあるため、パッケージと具体性を強化すれば保存率を伸ばせます "
        f"(エンゲージメント率={engagement_rate:.2f}%, 保存率={save_rate:.2f}%)。"
    )


def build_analysis(
    post: dict[str, Any],
    raw_metrics: dict[str, int],
    optional_metrics: dict[str, float],
    missing_metrics: list[str],
) -> dict[str, Any]:
    metrics: dict[str, float] = dict(raw_metrics)
    views = float(raw_metrics["views"])
    likes = float(raw_metrics["likes"])
    comments = float(raw_metrics["comments"])
    saves = float(raw_metrics["saves"])

    metrics["like_rate"] = pct(likes, views)
    metrics["comment_rate"] = pct(comments, views)
    metrics["save_rate"] = pct(saves, views)
    metrics["engagement_rate"] = pct(likes + comments + saves, views)

    signals = detect_content_signals(post)
    quantitative_available = len(missing_metrics) == 0 and metrics["views"] > 0
    if quantitative_available:
        why_engagement = build_why_engagement(post, metrics, signals)
    else:
        missing_label = ", ".join(missing_metrics) if missing_metrics else "views"
        why_engagement = [
            f"次の指標が不足しており、定量診断は限定的です: {missing_label}",
            "今回は実測値よりも、構成設計と保存導線の改善に重点を置いています。",
        ]
    save_improvements = build_save_improvements(metrics, signals, post)
    if quantitative_available:
        summary = build_summary(metrics)
    else:
        summary = "内容中心の分析を実行しました。完全な定量診断には views/likes/comments/saves が必要です。"
    strategy_alignment = build_strategy_alignment(
        post, metrics, optional_metrics, missing_metrics, signals
    )
    guardrail_flags = strategy_alignment["guardrail_flags"]

    analysis_markdown = "\n".join(
        [
            f"## 要約\n{summary}",
            "## なぜこのエンゲージメントになったか",
            join_lines(why_engagement),
            "## 保存数を伸ばす改善策",
            join_lines(save_improvements),
            "## 戦略整合性",
            f"- ミッション適合スコア: {strategy_alignment['mission_fit_score']}/100",
            f"- 判定ピラー: {strategy_alignment['detected_pillar_ja']}",
            (
                "- ガードレール警告: なし"
                if not guardrail_flags
                else "- ガードレール警告:\n" + join_lines(guardrail_flags)
            ),
        ]
    )

    return {
        "post": post,
        "metrics": metrics,
        "analysis": {
            "summary": summary,
            "why_engagement": why_engagement,
            "save_improvements": save_improvements,
            "strategy_alignment": strategy_alignment,
            "data_quality": {
                "quantitative_available": quantitative_available,
                "missing_metrics": missing_metrics,
            },
            "analysis_markdown": analysis_markdown,
        },
    }


def add_notion_property(
    properties: dict[str, Any],
    property_name: str,
    field_type: str,
    value: Any,
) -> None:
    if value is None:
        return
    if field_type == "title":
        properties[property_name] = {"title": split_rich_text(str(value))}
    elif field_type == "number":
        properties[property_name] = {"number": float(value)}
    elif field_type == "url":
        value_str = str(value).strip()
        if value_str:
            properties[property_name] = {"url": value_str}
    elif field_type == "date":
        value_str = str(value).strip()
        if value_str:
            properties[property_name] = {"date": {"start": value_str}}
    elif field_type == "rich_text":
        properties[property_name] = {"rich_text": split_rich_text(str(value))}
    else:
        raise ValueError(f"Unsupported Notion field type: {field_type}")


def is_compatible_field(expected_type: str, notion_type: str) -> bool:
    return expected_type == notion_type


def build_notion_payload(
    analysis_result: dict[str, Any],
    property_map: dict[str, str],
    available_property_types: dict[str, str] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    post = analysis_result["post"]
    metrics = analysis_result["metrics"]
    analysis = analysis_result["analysis"]

    title = (
        post.get("caption")
        or post.get("content_summary")
        or post.get("post_id")
        or "TikTok Post Analysis"
    )
    title = str(title)[:100]

    properties: dict[str, Any] = {}
    field_specs = {
        "title": ("title", title),
        "post_id": ("rich_text", post.get("post_id", "")),
        "url": ("url", post.get("url", "")),
        "published_at": ("date", post.get("published_at", "")),
        "views": ("number", metrics.get("views")),
        "likes": ("number", metrics.get("likes")),
        "comments": ("number", metrics.get("comments")),
        "saves": ("number", metrics.get("saves")),
        "engagement_rate": ("number", round(float(metrics.get("engagement_rate", 0.0)), 4)),
        "like_rate": ("number", round(float(metrics.get("like_rate", 0.0)), 4)),
        "comment_rate": ("number", round(float(metrics.get("comment_rate", 0.0)), 4)),
        "save_rate": ("number", round(float(metrics.get("save_rate", 0.0)), 4)),
        "content_summary": ("rich_text", post.get("content_summary", "")),
        "why_engagement": ("rich_text", join_lines(analysis.get("why_engagement", []))),
        "save_improvements": ("rich_text", join_lines(analysis.get("save_improvements", []))),
        "analysis_markdown": ("rich_text", analysis.get("analysis_markdown", "")),
    }

    skipped: list[str] = []
    for canonical_key, (field_type, value) in field_specs.items():
        prop_name = property_map.get(canonical_key)
        if prop_name:
            if available_property_types is not None:
                notion_type = available_property_types.get(prop_name)
                if notion_type is None:
                    skipped.append(f"{canonical_key}:missing_property({prop_name})")
                    continue
                if not is_compatible_field(field_type, notion_type):
                    skipped.append(
                        f"{canonical_key}:type_mismatch({field_type}!={notion_type})"
                    )
                    continue
            add_notion_property(properties, prop_name, field_type, value)
    return properties, skipped


def notion_request(url: str, method: str, headers: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Notion API error {exc.code}: {detail}") from exc


def notion_get(url: str, headers: dict[str, str]) -> dict[str, Any]:
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Notion API error {exc.code}: {detail}") from exc


def notion_headers(token: str, notion_version: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": notion_version,
    }


def resolve_data_source_id(
    token: str, database_id: str, notion_version: str
) -> str | None:
    headers = notion_headers(token, notion_version)
    data = notion_get(f"https://api.notion.com/v1/databases/{database_id}", headers)
    data_sources = data.get("data_sources") or []
    if not isinstance(data_sources, list) or not data_sources:
        return None
    first = data_sources[0]
    if not isinstance(first, dict):
        return None
    data_source_id = first.get("id")
    return data_source_id if isinstance(data_source_id, str) else None


def fetch_data_source_property_types(
    token: str, data_source_id: str, notion_version: str
) -> dict[str, str]:
    headers = notion_headers(token, notion_version)
    data = notion_get(f"https://api.notion.com/v1/data_sources/{data_source_id}", headers)
    properties = data.get("properties") or {}
    if not isinstance(properties, dict):
        return {}
    out: dict[str, str] = {}
    for name, prop in properties.items():
        if isinstance(name, str) and isinstance(prop, dict):
            prop_type = prop.get("type")
            if isinstance(prop_type, str):
                out[name] = prop_type
    return out


def auto_adjust_property_map(
    property_map: dict[str, str], available_properties: dict[str, str]
) -> dict[str, str]:
    available_names = set(available_properties.keys())
    adjusted = dict(property_map)
    for canonical, mapped_name in list(adjusted.items()):
        if mapped_name in available_names:
            continue
        for alias in CANONICAL_PROPERTY_ALIASES.get(canonical, []):
            if alias in available_names:
                adjusted[canonical] = alias
                break

    if "title" in adjusted and adjusted["title"] not in available_names:
        for name, prop_type in available_properties.items():
            if prop_type == "title":
                adjusted["title"] = name
                break
    return adjusted


def create_notion_page(
    token: str,
    database_id: str | None,
    data_source_id: str | None,
    notion_version: str,
    properties: dict[str, Any],
) -> dict[str, Any]:
    headers = notion_headers(token, notion_version)
    if data_source_id:
        parent = {"type": "data_source_id", "data_source_id": data_source_id}
    elif database_id:
        parent = {"type": "database_id", "database_id": database_id}
    else:
        raise ValueError("Either database_id or data_source_id is required.")
    payload = {"parent": parent, "properties": properties}
    return notion_request("https://api.notion.com/v1/pages", "POST", headers, payload)


def write_output(result: dict[str, Any], output_path: str | None) -> None:
    serialized = json.dumps(result, ensure_ascii=False, indent=2)
    if output_path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(serialized + "\n", encoding="utf-8")
    else:
        print(serialized)


def main() -> int:
    args = parse_args()
    try:
        if args.input:
            payload = load_json(args.input)
        elif args.url:
            payload = build_payload_from_url(args)
        else:
            raise ValueError("Either --input or --url is required.")
        post = extract_post(payload)
        strict_metrics = not args.allow_missing_metrics and not args.url
        metrics, missing_metrics = extract_metrics(payload, strict=strict_metrics)
        if missing_metrics and not args.allow_missing_metrics and args.url:
            raise ValueError(
                "URL mode requires metrics for full analysis. Provide --views --likes --comments --saves "
                "or rerun with --allow-missing-metrics for content-only analysis."
            )
        optional_metrics = extract_optional_metrics(payload)
        analysis_result = build_analysis(post, metrics, optional_metrics, missing_metrics)
        output: dict[str, Any] = {"result": analysis_result, "notion": {"status": "skipped"}}

        if args.dry_run:
            output["notion"]["status"] = "dry_run"
        else:
            if missing_metrics:
                raise ValueError(
                    "Notion write is blocked because required metrics are missing. "
                    "Provide views/likes/comments/saves first."
                )
            if not args.notion_token or (
                not args.notion_database_id and not args.notion_data_source_id
            ):
                raise ValueError(
                    "Notion credentials missing. Set NOTION_API_KEY and either "
                    "NOTION_DATA_SOURCE_ID or NOTION_DATABASE_ID, or pass equivalent args."
                )
            notion_data_source_id = args.notion_data_source_id
            if not notion_data_source_id and args.notion_database_id:
                notion_data_source_id = resolve_data_source_id(
                    args.notion_token, args.notion_database_id, args.notion_version
                )

            available_property_types: dict[str, str] | None = None
            if notion_data_source_id:
                available_property_types = fetch_data_source_property_types(
                    args.notion_token, notion_data_source_id, args.notion_version
                )

            property_map = load_property_map(args.property_map)
            if available_property_types and not args.property_map:
                property_map = auto_adjust_property_map(property_map, available_property_types)

            properties, skipped_fields = build_notion_payload(
                analysis_result,
                property_map,
                available_property_types=available_property_types,
            )
            if not properties:
                raise ValueError(
                    "No compatible Notion properties were found. Create at least one title property "
                    "and update property mapping."
                )
            notion_page = create_notion_page(
                token=args.notion_token,
                database_id=args.notion_database_id,
                data_source_id=notion_data_source_id,
                notion_version=args.notion_version,
                properties=properties,
            )
            output["notion"] = {
                "status": "created",
                "page_id": notion_page.get("id"),
                "url": notion_page.get("url"),
                "data_source_id": notion_data_source_id,
                "skipped_fields": skipped_fields,
            }

        write_output(output, args.output)
        return 0
    except Exception as exc:  # pylint: disable=broad-except
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
