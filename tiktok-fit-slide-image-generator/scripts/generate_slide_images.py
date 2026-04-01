#!/usr/bin/env python3
"""Generate slide images from a script markdown file."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = "data/pipeline/drafts/script.md"
DEFAULT_OUTPUT_ROOT = "data/pipeline/images"
DEFAULT_SYSTEM_PROMPT = str(SKILL_DIR / "references" / "nano-banana-system-prompt.md")
DEFAULT_REFERENCE_IMAGE = str(SKILL_DIR / "assets" / "kintaro-reference.jpg")

BIOLOGY_HINTS = (
    "作用機序",
    "メカニズム",
    "生体",
    "細胞",
    "受容体",
    "酵素",
    "ホルモン",
    "ミトコンドリア",
    "代謝",
    "神経伝達",
    "タンパク質合成",
    "免疫",
    "炎症",
    "atp",
)

HUMAN_HINTS = (
    "人",
    "人物",
    "男性",
    "女性",
    "トレーニー",
    "顔",
    "表情",
    "ポーズ",
    "悩む",
    "手元",
    "食べる",
)


@dataclass
class Slide:
    number: int
    text: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate images for each slide in a script markdown.")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Script file path. '@path' format is supported.")
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--post-slug", default="")
    parser.add_argument("--model", default="pro", help="Gemini model name. Keep 'pro' for this workflow.")
    parser.add_argument(
        "--prompt-profile",
        choices=["strict", "free"],
        default="strict",
        help="strict: apply configured image rules, free: remove style and mode constraints for trial output.",
    )
    parser.add_argument("--free", action="store_true", help="Shortcut for --prompt-profile free")
    parser.add_argument(
        "--backend",
        choices=["gemini", "dry-run", "antigravity"],
        default="antigravity",
        help="antigravity: prompt/manifest only for native Antigravity image generation",
    )
    parser.add_argument("--api-key", default="", help="If omitted, GEMINI_API_KEY is used.")
    parser.add_argument("--reference-image", default=DEFAULT_REFERENCE_IMAGE)
    parser.add_argument("--no-reference-image", action="store_true")
    parser.add_argument("--system-prompt-file", default=DEFAULT_SYSTEM_PROMPT)
    parser.add_argument("--manifest-out", default="")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--fail-fast", action="store_true")
    return parser.parse_args()


def strip_at_prefix(path_text: str) -> str:
    value = path_text.strip()
    if value.startswith("@"):
        return value[1:].strip()
    return value


def resolve_input_path(raw: str) -> Path:
    candidate = strip_at_prefix(raw) or DEFAULT_INPUT
    base = Path(candidate).expanduser()
    candidates: list[Path] = []
    if base.is_absolute():
        candidates.append(base)
    else:
        candidates.extend(
            [
                Path.cwd() / base,
                Path(base),
                Path("data/pipeline/drafts") / base,
            ]
        )

    seen: set[str] = set()
    for item in candidates:
        key = str(item)
        if key in seen:
            continue
        seen.add(key)
        if item.exists() and item.is_file():
            return item.resolve()

    raise FileNotFoundError(f"Input file not found: {raw}")


def slugify(text: str) -> str:
    value = unicodedata.normalize("NFKC", text).strip().lower()
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"[^a-z0-9\-ぁ-んァ-ン一-龥]", "", value)
    return value[:80] or "slides"


def parse_numbered_lines(markdown_text: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    patterns = [
        re.compile(r"^\s*(\d+)\s*枚目\s*[:：]\s*(.+?)\s*$"),
        re.compile(r"^\s*(?:slide|スライド)\s*(\d+)\s*[:：\-]\s*(.+?)\s*$", re.IGNORECASE),
    ]
    for line in markdown_text.splitlines():
        for pattern in patterns:
            matched = pattern.match(line)
            if not matched:
                continue
            out.append((int(matched.group(1)), clean_text(matched.group(2))))
            break
    return out


def parse_markdown_tables(markdown_text: str) -> list[tuple[int, str]]:
    lines = markdown_text.splitlines()
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.strip().startswith("|"):
            current.append(line.rstrip())
        else:
            if current:
                blocks.append(current)
                current = []
    if current:
        blocks.append(current)

    out: list[tuple[int, str]] = []
    for block in blocks:
        if len(block) < 3:
            continue
        header = split_table_row(block[0])
        separator = block[1].strip()
        if not re.search(r"-{3,}", separator):
            continue

        slide_idx = find_column_index(header, ("スライド", "slide"))
        text_idx = find_column_index(header, ("テキスト", "text"))
        if slide_idx < 0 or text_idx < 0:
            continue

        for row in block[2:]:
            cells = split_table_row(row)
            if len(cells) <= max(slide_idx, text_idx):
                continue
            matched = re.search(r"\d+", cells[slide_idx])
            if not matched:
                continue
            slide_number = int(matched.group())
            slide_text = clean_text(cells[text_idx])
            if slide_text:
                out.append((slide_number, slide_text))
    return out


def parse_slide_headers(markdown_text: str) -> list[tuple[int, str]]:
    lines = markdown_text.splitlines()
    header_pattern = re.compile(r"^\s*#{1,6}\s*(?:slide|スライド)\s*(\d+)\s*[:：\-]?\s*(.*)$", re.IGNORECASE)
    heads: list[tuple[int, int, str]] = []
    for idx, line in enumerate(lines):
        matched = header_pattern.match(line)
        if not matched:
            continue
        heads.append((idx, int(matched.group(1)), clean_text(matched.group(2))))

    out: list[tuple[int, str]] = []
    for i, (start_idx, slide_number, heading_tail) in enumerate(heads):
        end_idx = heads[i + 1][0] if i + 1 < len(heads) else len(lines)
        block = lines[start_idx + 1 : end_idx]
        text = extract_text_from_block(block)
        if not text:
            text = heading_tail
        if text:
            out.append((slide_number, clean_text(text)))
    return out


def extract_text_from_block(block_lines: list[str]) -> str:
    candidates: list[str] = []
    pointer = 0
    while pointer < len(block_lines):
        raw = block_lines[pointer].strip()
        normalized = clean_text(raw)
        if not normalized:
            pointer += 1
            continue

        is_text_label = ("テキスト" in normalized) or ("メインテキスト" in normalized)
        if is_text_label and ":" in normalized:
            after = normalized.split(":", 1)[1].strip()
            if after:
                candidates.append(after)
            else:
                gathered: list[str] = []
                next_pos = pointer + 1
                while next_pos < len(block_lines):
                    next_line = clean_text(block_lines[next_pos].strip())
                    if not next_line:
                        next_pos += 1
                        continue
                    if next_line.startswith("-") and any(
                        marker in next_line for marker in ("画像", "補足", "背景", "タイトル", "内容")
                    ):
                        break
                    if next_line.startswith("-") and "テキスト" in next_line:
                        break
                    gathered.append(next_line.strip("「」\"' "))
                    next_pos += 1
                if gathered:
                    candidates.append(" ".join(gathered))
                pointer = next_pos
                continue
        pointer += 1

    if not candidates:
        plain: list[str] = []
        for raw in block_lines:
            text = clean_text(raw.strip())
            if not text:
                continue
            if any(marker in text for marker in ("画像", "補足", "背景", "タイトル", "内容")):
                continue
            plain.append(text)
        if plain:
            candidates.append(" ".join(plain[:2]))

    if not candidates:
        return ""
    best = max(candidates, key=len)
    return clean_text(best)


def split_table_row(row: str) -> list[str]:
    text = row.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|"):
        text = text[:-1]
    return [cell.strip() for cell in text.split("|")]


def find_column_index(header_cells: list[str], candidates: tuple[str, ...]) -> int:
    for idx, cell in enumerate(header_cells):
        lowered = clean_text(cell).lower()
        for candidate in candidates:
            if candidate.lower() in lowered:
                return idx
    return -1


def clean_text(text: str) -> str:
    value = text
    value = re.sub(r"(?i)<br\s*/?>", "\n", value)
    value = re.sub(r"\*\*|__|`", "", value)
    value = value.replace("\\n", "\n")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def parse_slides(markdown_text: str) -> list[Slide]:
    parsed_sets = [
        parse_markdown_tables(markdown_text),
        parse_slide_headers(markdown_text),
        parse_numbered_lines(markdown_text),
    ]
    non_empty = [parsed for parsed in parsed_sets if parsed]
    if not non_empty:
        raise ValueError("No slide text found. Use numbered lines, slide headers, or markdown table format.")

    best = max(non_empty, key=len)
    indexed: dict[int, str] = {}
    for number, text in best:
        if not text:
            continue
        if number not in indexed or len(text) > len(indexed[number]):
            indexed[number] = text

    slides = [Slide(number=num, text=indexed[num]) for num in sorted(indexed.keys())]
    if not slides:
        raise ValueError("Slides were detected but slide text was empty.")
    return slides


def detect_mode(slide_text: str) -> str:
    lowered = slide_text.lower()
    if any(keyword in lowered for keyword in BIOLOGY_HINTS):
        return "B"
    return "A"


def needs_reference_image(slide_text: str) -> bool:
    lowered = slide_text.lower()
    return any(keyword in lowered for keyword in HUMAN_HINTS)


def build_user_prompt(slide: Slide, mode: str, use_reference: bool) -> str:
    mode_policy = (
        "Mode A: Keep text exactly as provided. No rewrite, no summary, no additions."
        if mode == "A"
        else "Mode B: Rewrite into child-friendly picture-book wording before rendering text."
    )

    ref_line = (
        "Use the attached reference image for the character, maintaining facial consistency."
        if use_reference
        else "Do not force a human character if it is unnecessary."
    )

    table_rule = ""
    if "|" in slide.text and "---" in slide.text:
        table_rule = "CRITICAL: This slide contains comparative table data. Render it as an intuitive, visually striking infographic/diagram (ポンチ絵) with icons, instead of a plain text table.\n"

    return (
        f"Create one image for slide {slide.number}.\n"
        f"{mode_policy}\n"
        "Visual constraints: Minimalist but high-impact design, extensive white space, simple shapes.\n"
        "Typography: Use extremely BOLD and LARGE fonts for key terms to make them pop on mobile screens.\n"
        "Background must be clean white (#FFFFFF). Aspect ratio must be 1:1.\n"
        f"{ref_line}\n"
        f"{table_rule}"
        "Text content:\n"
        "<<<TEXT\n"
        f"{slide.text}\n"
        "TEXT"
    )


def build_user_prompt_free(slide: Slide, use_reference: bool) -> str:
    ref_line = (
        "If a human character is needed, use the attached reference image as guidance."
        if use_reference
        else "A human character is optional."
    )
    
    table_rule = ""
    if "|" in slide.text and "---" in slide.text:
        table_rule = "CRITICAL: This slide contains comparative table data. Render it as an intuitive, visually striking infographic/diagram (ポンチ絵) with icons, instead of a plain text table.\n"

    return (
        f"Create one expressive and engaging image for slide {slide.number}.\n"
        "Use any visual style, composition, color palette, and detail level that best matches the message.\n"
        "Do not limit to minimalist style.\n"
        f"{ref_line}\n"
        f"{table_rule}"
        "Text to communicate in the image:\n"
        "<<<TEXT\n"
        f"{slide.text}\n"
        "TEXT"
    )


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def ensure_output_dir(root: Path, slug: str, overwrite: bool) -> Path:
    target = root / slug
    if target.exists() and not overwrite:
        suffix = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        target = root / f"{slug}_{suffix}"
    target.mkdir(parents=True, exist_ok=True)
    (target / "prompts").mkdir(parents=True, exist_ok=True)
    return target


def read_reference_image(path: Path) -> tuple[str, str]:
    mime_type, _ = mimetypes.guess_type(path.name)
    if not mime_type:
        mime_type = "image/jpeg"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return mime_type, data


def gemini_generate_image(
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    reference_image: tuple[str, str] | None,
    timeout: int,
) -> tuple[bytes, str]:
    model_name = urllib.parse.quote(model, safe="")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    parts: list[dict[str, Any]] = [{"text": user_prompt}]
    if reference_image:
        parts.append(
            {
                "inlineData": {
                    "mimeType": reference_image[0],
                    "data": reference_image[1],
                }
            }
        )

    payload: dict[str, Any] = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]},
    }
    if system_prompt.strip():
        payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

    req = urllib.request.Request(
        url=url,
        method="POST",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload).encode("utf-8"),
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            response_data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini API error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Gemini API connection error: {exc}") from exc

    for candidate in response_data.get("candidates", []):
        content = candidate.get("content", {})
        for part in content.get("parts", []):
            inline = part.get("inlineData") or part.get("inline_data")
            if not isinstance(inline, dict):
                continue
            raw = inline.get("data")
            if not isinstance(raw, str):
                continue
            mime = inline.get("mimeType") or inline.get("mime_type") or "image/png"
            return base64.b64decode(raw), str(mime)

    text_fallback: list[str] = []
    for candidate in response_data.get("candidates", []):
        content = candidate.get("content", {})
        for part in content.get("parts", []):
            if isinstance(part.get("text"), str):
                text_fallback.append(part["text"])
    joined = "\n".join(text_fallback).strip()
    raise RuntimeError(f"No image found in Gemini response. Text response: {joined[:500]}")


def extension_from_mime(mime_type: str) -> str:
    lower = mime_type.lower()
    if "jpeg" in lower or "jpg" in lower:
        return "jpg"
    if "webp" in lower:
        return "webp"
    return "png"


def main() -> int:
    args = parse_args()
    if args.free:
        args.prompt_profile = "free"
    input_path = resolve_input_path(args.input)
    output_root = Path(args.output_root)
    system_prompt_path = Path(args.system_prompt_file)
    if not system_prompt_path.exists():
        raise FileNotFoundError(f"System prompt file not found: {system_prompt_path}")
    system_prompt = read_text(system_prompt_path)
    if args.prompt_profile == "free":
        system_prompt = ""

    reference_path = Path(args.reference_image)
    reference_data: tuple[str, str] | None = None
    if not args.no_reference_image and reference_path.exists():
        reference_data = read_reference_image(reference_path)

    source = read_text(input_path)
    slides = parse_slides(source)

    slug = args.post_slug.strip() or slugify(input_path.stem)
    output_dir = ensure_output_dir(output_root, slug, overwrite=args.overwrite)

    api_key = args.api_key.strip()
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if args.backend == "gemini" and not api_key:
        raise RuntimeError("GEMINI_API_KEY is required for backend=gemini. Use --backend dry-run for prompt-only output.")

    manifest: dict[str, Any] = {
        "ok": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "backend": args.backend,
        "model": args.model,
        "prompt_profile": args.prompt_profile,
        "input_script": str(input_path),
        "output_dir": str(output_dir),
        "system_prompt_file": str(system_prompt_path),
        "reference_image": str(reference_path) if reference_data else "",
        "slides": [],
    }

    any_error = False
    for slide in slides:
        mode = detect_mode(slide.text)
        wants_human = needs_reference_image(slide.text)
        use_reference = bool(reference_data and wants_human)
        if args.prompt_profile == "free":
            prompt = build_user_prompt_free(slide, use_reference=use_reference)
        else:
            prompt = build_user_prompt(slide, mode=mode, use_reference=use_reference)

        prompt_path = output_dir / "prompts" / f"slide_{slide.number:02d}.prompt.txt"
        prompt_path.write_text(prompt, encoding="utf-8")

        slide_log: dict[str, Any] = {
            "slide_number": slide.number,
            "mode": mode,
            "uses_reference_image": use_reference,
            "source_text": slide.text,
            "prompt_path": str(prompt_path),
            "status": "",
            "image_path": "",
            "error": "",
        }

        if args.backend in ("dry-run", "antigravity"):
            slide_log["status"] = "dry-run" if args.backend == "dry-run" else "pending-antigravity"
            if args.backend == "antigravity":
                slide_log["image_path"] = str(output_dir / f"slide_{slide.number:02d}.png")
            manifest["slides"].append(slide_log)
            continue

        last_error = ""
        attempts = max(1, args.max_retries + 1)
        for attempt in range(1, attempts + 1):
            try:
                image_bytes, mime_type = gemini_generate_image(
                    api_key=api_key,
                    model=args.model,
                    system_prompt=system_prompt,
                    user_prompt=prompt,
                    reference_image=reference_data if use_reference else None,
                    timeout=args.timeout,
                )
                ext = extension_from_mime(mime_type)
                image_path = output_dir / f"slide_{slide.number:02d}.{ext}"
                image_path.write_bytes(image_bytes)
                slide_log["status"] = "ok"
                slide_log["image_path"] = str(image_path)
                break
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)
                if attempt >= attempts:
                    slide_log["status"] = "error"
                    slide_log["error"] = last_error
                    any_error = True
                    if args.fail_fast:
                        break
        manifest["slides"].append(slide_log)
        if args.fail_fast and slide_log["status"] == "error":
            break

    if any_error:
        manifest["ok"] = False

    manifest_path = Path(args.manifest_out) if args.manifest_out else output_dir / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "ok": manifest["ok"],
        "input_script": str(input_path),
        "output_dir": str(output_dir),
        "manifest": str(manifest_path),
        "model": args.model,
        "prompt_profile": args.prompt_profile,
        "backend": args.backend,
        "slide_count": len(manifest["slides"]),
        "success_count": sum(1 for s in manifest["slides"] if s["status"] == "ok"),
        "error_count": sum(1 for s in manifest["slides"] if s["status"] == "error"),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if any_error else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(1)
