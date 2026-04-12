#!/usr/bin/env python3
"""
render_slides.py - tiktok-fit-slide-renderer メインスクリプト

Pillow で日本語テキスト主体のカルーセル画像（1080×1080 PNG）を生成する。
SVG中間形式なし、直接PNG描画。Windows/macOS/Linux 完全互換。

Usage:
    python3 render_slides.py --parse --input <script.md>
    python3 render_slides.py --validate --manifest <manifest.yaml>
    python3 render_slides.py --render --manifest <manifest.yaml>
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml が必要です: pip install PyYAML", file=sys.stderr)
    sys.exit(1)

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow が必要です: pip install Pillow>=12.0.0", file=sys.stderr)
    sys.exit(1)

try:
    import budoux
except ImportError:
    print("ERROR: budoux が必要です: pip install budoux", file=sys.stderr)
    sys.exit(1)


# ──────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
CONFIG_PATH = SKILL_DIR / "templates" / "style_config.json"
FONT_DIR = SKILL_DIR / "fonts"
DRAFT_DIR = SKILL_DIR / "data" / "pipeline" / "drafts"
_env_image_dir = os.environ.get("BB_IMAGE_DIR")
IMAGE_DIR = Path(_env_image_dir) if _env_image_dir else SKILL_DIR / "output" / "投稿画像"
FEEDBACK_LOG = SKILL_DIR / "data" / "pipeline" / "feedback_log.jsonl"


# ──────────────────────────────────────────────
# Config utilities
# ──────────────────────────────────────────────

def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def yaml_literal_representer(dumper, data):
    """複数行文字列を YAML literal block style で出力する"""
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.add_representer(str, yaml_literal_representer)


# ──────────────────────────────────────────────
# Font loader
# ──────────────────────────────────────────────

_font_cache: dict = {}


def load_font(weight: str, pointsize: int, config: dict) -> ImageFont.FreeTypeFont:
    """Variable font から指定weightのフォントを取得（キャッシュあり）"""
    key = (weight, pointsize)
    if key in _font_cache:
        return _font_cache[key]

    font_path = FONT_DIR / config["font_file"]
    if not font_path.exists():
        raise FileNotFoundError(
            f"フォントファイルが見つかりません: {font_path}\n"
            f"Noto Sans JP を fonts/ に配置してください。"
        )

    font = ImageFont.truetype(str(font_path), pointsize)
    try:
        font.set_variation_by_name(weight.encode("utf-8"))
    except (OSError, AttributeError):
        # 静的フォントの場合はそのまま使う
        pass

    _font_cache[key] = font
    return font


# ──────────────────────────────────────────────
# Phase 1: Parse (Markdown → YAML)
# ──────────────────────────────────────────────

LAYER_HEADER_PATTERN = re.compile(
    r"^(メイン|サブ|補足)[・·](大|中|小)[・·](黒|赤|青|#[0-9A-Fa-f]{3,6})\s*$"
)


def parse_text_slide(block: str) -> list[dict]:
    """スライドブロックからレイヤーをパースする（新テキスト形式）"""
    layers = []
    lines = block.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        m = LAYER_HEADER_PATTERN.match(line)
        if not m:
            i += 1
            continue

        layer_name, size, color = m.group(1), m.group(2), m.group(3)
        text_lines = []
        j = i + 1
        while j < len(lines):
            next_line = lines[j].rstrip()
            if LAYER_HEADER_PATTERN.match(next_line.strip()):
                break
            if next_line.strip().startswith("感情設計"):
                break
            if next_line.strip().startswith("##"):
                break
            if next_line.strip():
                text_lines.append(next_line.strip())
            j += 1

        if text_lines:
            layers.append({
                "layer": layer_name,
                "text": "\n".join(text_lines),
                "size": size,
                "color": color,
            })
        i = j

    return layers


def parse_summary_table(block: str) -> list[list[str]]:
    """Markdown表をパースして2次元配列を返す"""
    rows = []
    for line in block.split("\n"):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.split("|") if c.strip() or c == ""]
        # 先頭と末尾の空セルを除去
        cells = [c.strip() for c in stripped.split("|")][1:-1]
        if not cells:
            continue
        # セパレータ行（|---|---|）をスキップ
        if all(re.match(r"^[-: ]+$", c.strip()) for c in cells):
            continue
        rows.append([c.strip() for c in cells])
    return rows


def parse_carousel_markdown(markdown_text: str) -> list[dict]:
    """カルーセル台本Markdownをスライドデータリストに変換する"""
    slide_pattern = re.compile(
        r"^##\s*スライド\s*(\d+)\s*[（(]([^）)]*)[）)]",
        re.MULTILINE,
    )
    matches = list(slide_pattern.finditer(markdown_text))
    if not matches:
        raise ValueError(
            "スライドが見つかりません。\n"
            "'## スライド N（役割）' 形式で記述してください。"
        )

    slides = []
    for i, m in enumerate(matches):
        number = int(m.group(1))
        role = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown_text)
        block = markdown_text[start:end]

        # 感情設計
        emotion_m = re.search(r"感情設計[：:]\s*(.+)", block)
        emotion = emotion_m.group(1).strip() if emotion_m else ""

        # まとめ表かテキストスライドかを判定
        is_summary = "まとめ表" in role
        slide: dict = {
            "number": number,
            "role": role,
            "emotion": emotion,
            "skip": False,
            "canvas_override": {},
        }

        if is_summary:
            slide["type"] = "table"
            slide["table"] = parse_summary_table(block)
        else:
            slide["type"] = "text"
            slide["layers"] = parse_text_slide(block)

        slides.append(slide)

    return slides


def cmd_parse(args) -> int:
    input_path = Path(args.input).expanduser()
    if not input_path.is_absolute():
        for base in [Path.cwd(), DRAFT_DIR]:
            cand = base / input_path
            if cand.exists():
                input_path = cand
                break

    if not input_path.exists():
        print(f"ERROR: 入力ファイルが見つかりません: {args.input}", file=sys.stderr)
        return 1

    config = load_config()
    text = input_path.read_text(encoding="utf-8")
    slides = parse_carousel_markdown(text)

    out_dir = Path(args.output_dir) if args.output_dir else DRAFT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    slug = re.sub(r"[^\w\-]", "_", input_path.stem)[:40]
    manifest_path = out_dir / f"{slug}_render_manifest.yaml"

    manifest = {
        "meta": {
            "script_source": str(input_path),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_slides": len(slides),
        },
        "canvas": config["canvas"],
        "slides": slides,
    }

    with manifest_path.open("w", encoding="utf-8") as f:
        yaml.dump(
            manifest, f, allow_unicode=True, default_flow_style=False,
            sort_keys=False, indent=2,
        )

    print(f"\n台本パース完了: {len(slides)} 枚")
    print(f"  manifest → {manifest_path}\n")
    print(f"{'No':>3}  {'役割':<10}  {'タイプ':<6}  {'感情設計':<15}")
    print(f"{'─'*3}  {'─'*10}  {'─'*6}  {'─'*15}")
    for s in slides:
        t = s.get("type", "text")
        skip = " [SKIP]" if s.get("skip") else ""
        layer_info = f"(×{len(s.get('layers', []))})" if t == "text" else f"({len(s.get('table', []))}行)"
        print(f"{s['number']:>3}  {s.get('role',''):<10}  {t:<6}  {s.get('emotion',''):<15}  {layer_info}{skip}")

    # バリデーション警告を表示
    errors, warnings = validate_manifest(manifest)
    if warnings:
        print(f"\nWARNING ({len(warnings)}件):")
        for w in warnings:
            print(f"  ⚠ {w}")

    print(f"\n次のステップ:")
    print(f"  python3 {Path(__file__).name} --validate --manifest {manifest_path}")
    return 0


# ──────────────────────────────────────────────
# Phase 2: Validate
# ──────────────────────────────────────────────

def estimate_text_width(text: str, pointsize: int) -> float:
    """テキスト幅の概算"""
    width = 0.0
    for ch in text:
        if ord(ch) > 0x7F:
            width += pointsize * 0.95
        else:
            width += pointsize * 0.5
    return width


def validate_manifest(manifest: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    config = load_config()
    size_map = config["size_map"]
    canvas = {**config["canvas"], **manifest.get("canvas", {})}
    usable_w = canvas["width"] - canvas["margin"] * 2

    slides = manifest.get("slides", [])
    if not slides:
        errors.append("スライドが0枚です。")
        return errors, warnings

    active = [s for s in slides if not s.get("skip")]
    if not active:
        errors.append("全スライドが skip: true になっています。")

    nums = [s["number"] for s in slides]
    if len(nums) != len(set(nums)):
        errors.append("スライド番号に重複があります。")

    for slide in active:
        n = slide["number"]
        stype = slide.get("type", "text")

        if stype == "text":
            layers = slide.get("layers", [])
            if not layers:
                warnings.append(f"スライド{n}: レイヤーが0個です")
                continue

            for layer in layers:
                size = layer.get("size", "中")
                color = layer.get("color", "黒")
                text = layer.get("text", "")

                if size not in ("大", "中", "小"):
                    errors.append(f"スライド{n}[{layer.get('layer')}]: size '{size}' 不正")
                if color not in ("黒", "赤", "青") and not color.startswith("#"):
                    errors.append(f"スライド{n}[{layer.get('layer')}]: color '{color}' 不正")
                if not text.strip():
                    warnings.append(f"スライド{n}[{layer.get('layer')}]: テキストが空")
                    continue

                if size in size_map:
                    ps = size_map[size]["pointsize"]
                    for line in text.split("\n"):
                        est = estimate_text_width(line, ps)
                        if est > usable_w:
                            warnings.append(
                                f"スライド{n}[{layer.get('layer')}]: 「{line[:12]}…」"
                                f"幅超過の可能性（推定 {est:.0f}px > {usable_w}px）"
                            )
                            break

        elif stype == "table":
            table = slide.get("table", [])
            if not table:
                warnings.append(f"スライド{n}: 表が空です")
                continue
            if len(table[0]) > 5:
                warnings.append(f"スライド{n}: 表の列数が5を超えています（{len(table[0])}列）")

    return errors, warnings


def cmd_validate(args) -> int:
    mpath = Path(args.manifest)
    if not mpath.exists():
        print(f"ERROR: {args.manifest} が見つかりません", file=sys.stderr)
        return 1

    with mpath.open(encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    errors, warnings = validate_manifest(manifest)
    slides = manifest.get("slides", [])
    active = [s for s in slides if not s.get("skip")]

    print(f"\nバリデーション: {len(slides)}枚 (生成対象: {len(active)}枚)")
    for e in errors:
        print(f"  ✗ {e}")
    for w in warnings:
        print(f"  ⚠ {w}")
    if not errors and not warnings:
        print("  ✓ 問題なし")

    if errors:
        print("\n→ エラーを修正してください")
        return 1

    print(f"\n→ 生成を開始するには:")
    print(f"  python3 {Path(__file__).name} --render --manifest {mpath}")
    return 0


# ──────────────────────────────────────────────
# Phase 3: Render (Pillow direct draw)
# ──────────────────────────────────────────────

_budoux_parser = None


def get_budoux_parser():
    global _budoux_parser
    if _budoux_parser is None:
        _budoux_parser = budoux.load_default_japanese_parser()
    return _budoux_parser


def split_phrase_by_chars(phrase: str, max_width: int, font: ImageFont.FreeTypeFont) -> list[str]:
    """フレーズが長すぎる場合、文字単位で分割する（記号・スペース優先）"""
    if font.getlength(phrase) <= max_width:
        return [phrase]

    # 好ましい区切り文字（これらの直後で分割を優先）
    break_chars = set(" 　×÷＋－+-*/()（）[]、。!?！？=＝")
    lines = []
    current = ""
    last_break_pos = -1

    for i, ch in enumerate(phrase):
        test = current + ch
        if font.getlength(test) > max_width and current:
            # 区切り文字位置まで戻って折り返す
            if last_break_pos > 0:
                lines.append(current[:last_break_pos + 1].rstrip())
                current = current[last_break_pos + 1:] + ch
                last_break_pos = -1
            else:
                lines.append(current)
                current = ch
        else:
            current = test
            if ch in break_chars:
                last_break_pos = len(current) - 1

    if current:
        lines.append(current)
    return lines


def wrap_japanese_line(text: str, max_width: int, font: ImageFont.FreeTypeFont) -> list[str]:
    """BudouXで日本語の折り返し + 文字単位フォールバック"""
    if not text:
        return [""]

    parser = get_budoux_parser()
    phrases = parser.parse(text)

    lines = []
    current = ""
    for phrase in phrases:
        # フレーズ単体が広すぎる場合は文字単位で分割
        if font.getlength(phrase) > max_width:
            if current:
                lines.append(current)
                current = ""
            char_lines = split_phrase_by_chars(phrase, max_width, font)
            lines.extend(char_lines[:-1])
            current = char_lines[-1] if char_lines else ""
            continue

        test = current + phrase
        if font.getlength(test) > max_width and current:
            lines.append(current)
            current = phrase
        else:
            current = test

    if current:
        lines.append(current)
    return lines if lines else [""]


def split_by_numbers(text: str, base_color: str, number_color: str, pattern: re.Pattern) -> list[tuple]:
    """テキストを(文字列, 色)のタプルに分割（数値自動色分け）"""
    fragments = []
    last_end = 0
    for m in pattern.finditer(text):
        if m.start() > last_end:
            fragments.append((text[last_end:m.start()], base_color))
        fragments.append((m.group(), number_color))
        last_end = m.end()
    if last_end < len(text):
        fragments.append((text[last_end:], base_color))
    return fragments if fragments else [(text, base_color)]


def resolve_color(color: str, color_map: dict) -> str:
    """色名(黒/赤/青)またはhex(#xxx)をhex値に変換"""
    if color.startswith("#"):
        return color
    return color_map.get(color, "#1a1a1a")


def draw_centered_fragments(draw, fragments, font, center_x: float, y: float):
    """色分けされたフラグメントを水平中央揃えで描画"""
    total_width = sum(font.getlength(f[0]) for f in fragments)
    x = center_x - total_width / 2
    for text, color in fragments:
        draw.text((x, y), text, font=font, fill=color, anchor="la")
        x += font.getlength(text)


def find_fit_pointsize(text_lines: list[str], base_pointsize: int, weight: str,
                      max_width: int, config: dict) -> tuple[int, ImageFont.FreeTypeFont, list[str]]:
    """フォントサイズ自動調整。戦略:
    1. 各user行が折り返しなしで収まる最大pointsizeを探す
    2. 失敗なら、適切に折り返した上で最大pointsizeを探す
    3. それでもダメなら、最小サイズで強制文字分割
    最小pointsizeは base*0.35 まで縮小を許容。
    """
    min_pointsize = max(int(base_pointsize * 0.35), 20)

    # 戦略1: 折り返しなしで全行が収まる最大サイズ
    for ps in range(base_pointsize, min_pointsize - 1, -2):
        font = load_font(weight, ps, config)
        if all(font.getlength(line) <= max_width for line in text_lines if line):
            return ps, font, list(text_lines)

    # 戦略2: 折り返しを許容して最大サイズ
    for ps in range(base_pointsize, min_pointsize - 1, -2):
        font = load_font(weight, ps, config)
        all_wrapped: list[str] = []
        all_fit = True
        for line in text_lines:
            wrapped = wrap_japanese_line(line, max_width, font)
            for wl in wrapped:
                if font.getlength(wl) > max_width:
                    all_fit = False
                    break
            if not all_fit:
                break
            all_wrapped.extend(wrapped)
        if all_fit:
            return ps, font, all_wrapped

    # 戦略3: 最小サイズで強制文字分割
    font = load_font(weight, min_pointsize, config)
    all_wrapped = []
    for line in text_lines:
        wrapped = split_phrase_by_chars(line, max_width, font)
        all_wrapped.extend(wrapped)
    return min_pointsize, font, all_wrapped


def calculate_layer_height(layer: dict, config: dict, max_width: int) -> tuple[int, list[list[tuple]], ImageFont.FreeTypeFont, int]:
    """レイヤーの総高さと、各行のフラグメント、採用フォント、ラインスペーシングを返す。
    テキストがmax_widthに収まらない場合は自動でフォント縮小を行う。"""
    size = layer.get("size", "中")
    size_info = config["size_map"][size]
    base_pointsize = size_info["pointsize"]
    weight = size_info["weight"]
    line_spacing_base = size_info["line_spacing"]

    color_map = config["color_map"]
    base_color = resolve_color(layer.get("color", "黒"), color_map)
    number_color = config["number_color"]
    pattern = re.compile(config["number_pattern"])

    # 明示的な改行を尊重して自動フィット
    raw_lines = layer["text"].split("\n")
    pointsize, font, wrapped_lines = find_fit_pointsize(
        raw_lines, base_pointsize, weight, max_width, config
    )
    # line_spacingも比例縮小
    line_spacing = int(line_spacing_base * pointsize / base_pointsize)

    # 各行をフラグメント化
    all_lines_fragments = []
    for line in wrapped_lines:
        if config.get("number_auto_colorize"):
            fragments = split_by_numbers(line, base_color, number_color, pattern)
        else:
            fragments = [(line, base_color)]
        all_lines_fragments.append(fragments)

    # 高さを計算
    n_lines = len(all_lines_fragments)
    ascent, descent = font.getmetrics()
    line_height = ascent + descent
    total_height = line_height * n_lines + line_spacing * max(0, n_lines - 1)

    return total_height, all_lines_fragments, font, line_spacing


def render_text_slide(slide_data: dict, config: dict, output_path: Path) -> dict:
    """テキストスライドをPillowで直接描画する"""
    canvas = {**config["canvas"], **slide_data.get("canvas_override", {})}
    w = canvas["width"]
    h = canvas["height"]
    bg = canvas["background"]
    margin = canvas["margin"]
    usable_w = w - 2 * margin
    usable_h = h - 2 * margin
    vpad = config["vertical_padding"]

    img = Image.new("RGB", (w, h), bg)
    draw = ImageDraw.Draw(img)

    layers = slide_data.get("layers", [])
    if not layers:
        img.save(output_path, "PNG", optimize=True)
        return {"status": "ok", "layers": 0}

    # 各レイヤーの高さと行フラグメントを計算（自動フィット済み）
    layer_data = []
    for layer in layers:
        height, frags, font, line_spacing = calculate_layer_height(layer, config, usable_w)
        layer_data.append({
            "layer": layer,
            "height": height,
            "lines_fragments": frags,
            "font": font,
            "line_spacing": line_spacing,
        })

    # 総高さ（レイヤー間パディング含む）
    total_h = sum(ld["height"] for ld in layer_data) + vpad * max(0, len(layer_data) - 1)

    # 垂直中央配置の開始y
    start_y = margin + (usable_h - total_h) / 2
    center_x = w / 2

    # 各レイヤーを描画
    current_y = start_y
    for ld in layer_data:
        font = ld["font"]
        line_spacing = ld["line_spacing"]
        ascent, descent = font.getmetrics()
        line_height = ascent + descent

        y = current_y
        for fragments in ld["lines_fragments"]:
            draw_centered_fragments(draw, fragments, font, center_x, y)
            y += line_height + line_spacing

        current_y += ld["height"] + vpad

    img.save(output_path, "PNG", optimize=True)
    return {"status": "ok", "layers": len(layers)}


def render_summary_table(slide_data: dict, config: dict, output_path: Path) -> dict:
    """まとめ表スライドを描画する"""
    canvas = {**config["canvas"], **slide_data.get("canvas_override", {})}
    w = canvas["width"]
    h = canvas["height"]
    bg = canvas["background"]
    margin = canvas["margin"]

    table = slide_data.get("table", [])
    if not table:
        return {"status": "error", "error": "table empty"}

    tbl_cfg = config["table"]
    border_color = tbl_cfg["border_color"]
    border_width = tbl_cfg["border_width"]

    img = Image.new("RGB", (w, h), bg)
    draw = ImageDraw.Draw(img)

    rows = len(table)
    cols = len(table[0])
    usable_w = w - 2 * margin
    usable_h = h - 2 * margin
    cell_w = usable_w / cols
    cell_h = usable_h / rows

    number_color = config["number_color"]
    pattern = re.compile(config["number_pattern"])

    for r, row in enumerate(table):
        is_header = (r == 0)
        weight = tbl_cfg["header_weight"] if is_header else tbl_cfg["cell_weight"]
        pointsize = tbl_cfg["header_pointsize"] if is_header else tbl_cfg["cell_pointsize"]
        font = load_font(weight, pointsize, config)

        for c, cell_text in enumerate(row):
            x0 = margin + c * cell_w
            y0 = margin + r * cell_h
            x1 = x0 + cell_w
            y1 = y0 + cell_h

            # セル背景（ヘッダーのみ）
            if is_header:
                draw.rectangle([x0, y0, x1, y1], fill=tbl_cfg["header_bg"])

            # 枠線
            draw.rectangle([x0, y0, x1, y1], outline=border_color, width=border_width)

            # テキスト色
            if is_header:
                base_color = tbl_cfg["header_fg"]
            else:
                base_color = "#1a1a1a"

            # 数値自動色分け（ヘッダー以外）
            if config.get("number_auto_colorize") and not is_header:
                fragments = split_by_numbers(cell_text, base_color, number_color, pattern)
            else:
                fragments = [(cell_text, base_color)]

            # セル内中央配置
            cx = x0 + cell_w / 2
            total_text_w = sum(font.getlength(f[0]) for f in fragments)
            ascent, descent = font.getmetrics()
            text_h = ascent + descent
            cy = y0 + (cell_h - text_h) / 2

            tx = cx - total_text_w / 2
            for text, color in fragments:
                draw.text((tx, cy), text, font=font, fill=color, anchor="la")
                tx += font.getlength(text)

    img.save(output_path, "PNG", optimize=True)
    return {"status": "ok", "rows": rows, "cols": cols}


def render_slide(slide_data: dict, config: dict, out_dir: Path) -> dict:
    n = slide_data["number"]
    png_path = out_dir / f"slide_{n:02d}.png"

    try:
        stype = slide_data.get("type", "text")
        if stype == "table":
            result = render_summary_table(slide_data, config, png_path)
        else:
            result = render_text_slide(slide_data, config, png_path)
        return {
            "slide_number": n,
            "role": slide_data.get("role", ""),
            "type": stype,
            "png_path": str(png_path),
            "status": result["status"],
            "error": result.get("error", ""),
        }
    except Exception as e:
        return {
            "slide_number": n,
            "role": slide_data.get("role", ""),
            "png_path": str(png_path),
            "status": "error",
            "error": str(e),
        }


def render_all(manifest: dict, out_dir: Path) -> dict:
    config = load_config()
    if "canvas" in manifest:
        config["canvas"] = {**config["canvas"], **manifest["canvas"]}

    slides = [s for s in manifest.get("slides", []) if not s.get("skip")]
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n画像生成: {len(slides)}枚 → {out_dir}\n")

    results = []
    for slide in slides:
        n = slide["number"]
        role = slide.get("role", "")
        print(f"  [{n:02d}] {role:<12}", end=" ... ", flush=True)
        log = render_slide(slide, config, out_dir)
        results.append(log)
        if log["status"] == "ok":
            print("✓ OK")
        else:
            print(f"✗ {log['error'][:60]}")

    ok_count = sum(1 for r in results if r["status"] == "ok")
    err_count = len(results) - ok_count

    manifest_json = {
        "ok": err_count == 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "output_dir": str(out_dir),
        "slide_count": len(results),
        "success_count": ok_count,
        "error_count": err_count,
        "slides": results,
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest_json, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\n完了: 成功 {ok_count} / 失敗 {err_count}")
    print(f"出力: {out_dir}")

    return manifest_json


def cmd_render(args) -> int:
    mpath = Path(args.manifest)
    if not mpath.exists():
        print(f"ERROR: {args.manifest} が見つかりません", file=sys.stderr)
        return 1

    with mpath.open(encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    if not args.skip_validate:
        errors, _ = validate_manifest(manifest)
        if errors:
            print("バリデーションエラーがあります。--validate で確認してください")
            return 1

    slug = mpath.stem.replace("_render_manifest", "")
    out_dir = Path(args.output_dir) if args.output_dir else IMAGE_DIR / slug

    result = render_all(manifest, out_dir)
    return 0 if result["ok"] else 1


# ──────────────────────────────────────────────
# Feedback logging
# ──────────────────────────────────────────────

def log_feedback(entry: dict):
    """フィードバックをJSONLに追記する"""
    FEEDBACK_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry_with_ts = {
        "ts": datetime.now(timezone.utc).isoformat(),
        **entry,
    }
    with FEEDBACK_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry_with_ts, ensure_ascii=False) + "\n")


def cmd_log(args) -> int:
    """フィードバックログに記録するだけのサブコマンド"""
    entry = json.loads(args.entry)
    log_feedback(entry)
    print("ログに記録しました")
    return 0


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser(description="tiktok-fit-slide-renderer")
    p.add_argument("--parse", action="store_true")
    p.add_argument("--validate", action="store_true")
    p.add_argument("--render", action="store_true")
    p.add_argument("--log", action="store_true", help="フィードバックログ記録")
    p.add_argument("--input", help="台本Markdownファイル")
    p.add_argument("--manifest", help="manifest.yaml")
    p.add_argument("--output-dir", help="出力ディレクトリ")
    p.add_argument("--skip-validate", action="store_true")
    p.add_argument("--entry", help="ログエントリ(JSON)")
    args = p.parse_args()

    if args.parse:
        if not args.input:
            print("ERROR: --parse には --input が必要です", file=sys.stderr)
            return 1
        return cmd_parse(args)
    elif args.validate:
        if not args.manifest:
            print("ERROR: --validate には --manifest が必要です", file=sys.stderr)
            return 1
        return cmd_validate(args)
    elif args.render:
        if not args.manifest:
            print("ERROR: --render には --manifest が必要です", file=sys.stderr)
            return 1
        return cmd_render(args)
    elif args.log:
        if not args.entry:
            print("ERROR: --log には --entry が必要です", file=sys.stderr)
            return 1
        return cmd_log(args)
    else:
        p.print_help()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
