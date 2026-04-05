# SVG→PNG 変換 × 日本語テキストレンダリング調査レポート（2025-2026）

**調査日**: 2026-04-05
**調査対象**: macOS + Python + 日本語テキスト中心 + 1:1 PNG（1080×1080）での画像カルーセル生成
**用途**: ミニマルデザインの図解（テキスト中心）を Claude Code (CLI) から生成するスキル構築

---

## エグゼクティブサマリー（先に結論）

**最有力推奨**: **Pillow 12.x による直接 PNG 描画**（SVG を経由しない）
**理由**: 日本語 CJK テキスト中心のミニマルデザインでは SVG 中間表現の利点（複雑なベクターグラフィックス）がほぼ活きず、逆に SVG→PNG 変換ツールの日本語フォント解決の落とし穴（fontconfig、librsvg の Hiragino 問題、tofu 化）を全て回避できるため。

**2番手**: **resvg（resvg-py 0.2.x）** ＋ Noto Sans CJK JP を明示ロード
**理由**: システムフォント非依存で再現性が高く、macOS/Linux/Windows でピクセル同一の結果を出せる。SVG テンプレート運用が必要なら最適。

**非推奨**: **cairosvg / svglib** — 両者とも「Japanese text の rendering は poorly supported」と公式ドキュメントに明記されている。

---

## 1. SVG→PNG 変換ツールの最新状況（2025-2026）

### 1.1 Python Pillow (PIL)

| 項目 | 内容 |
|---|---|
| 最新安定版 | **12.2.0**（2026年時点）/ 12.0.0 は **2025-10-15** リリース |
| Python 対応 | Python 3.14 正式対応（12.0.0〜） |
| SVG 対応 | **ネイティブ非対応**。Pillow はラスター画像ライブラリ |
| 日本語描画 | TrueType/OpenType フォント経由で完全対応、Raqm 連携で高品質テキストレイアウト |

**Pillow 12.0.0 の主要新機能**（2025-10-15 リリース）:
- `PIL.ImageText.Text` クラスが新設（フォントとテキストをより簡潔に扱える API）
- `embed_color()`, `stroke()`, `get_length()`, `get_bbox()` メソッド追加
- `FontFile.to_imagefont()` 追加（BDF/PCF → ImageFont 変換）
- ImageDraw テキストメソッドに `features` / `language` パラメータ追加（OpenType feature 対応）
- Pillow 11.x で zlib-ng による PNG 圧縮が **2倍以上高速化**

**日本語描画に必要な依存**（Pillow の FreeType + Raqm 連携）:
- **FreeType**: TrueType/OpenType スケーラブルフォント必須
- **Raqm**: 非英語テキストの複雑レイアウト処理（日本語で推奨される）
- **HarfBuzz + FriBidi**: 双方向テキスト/シェーピング

Raqm レイアウトが利用可能な環境では自動的に使用され、**非英語テキストでは公式推奨**とされている（Pillow 公式ドキュメント）。

### 1.2 cairosvg

| 項目 | 内容 |
|---|---|
| 現状 | SVG 1.1 → PNG/PDF/PS 変換。Cairo ベース |
| Python 対応 | 3.6+ |
| 日本語対応 | **公式に "poorly supported" と明記** |
| 右横書き（RTL）/ 縦書き | **全く非対応** |
| 採用判断 | 日本語中心用途では **非推奨** |

公式ドキュメントより引用:
> "Text and features related to fonts are poorly supported. Other languages, and particularly those based on right-to-left or top-to-bottom directions are not supported at all."

### 1.3 svglib

| 項目 | 内容 |
|---|---|
| 現状 | SVG → ReportLab Drawing → PNG/JPG/GIF |
| 日本語対応 | **不完全**（公式に "may produce issues with fonts and text" と明記） |
| 未対応機能 | gradients、patterns、markers、clipping paths |

svglib の GitHub issue / Stack Overflow でも **日本語フォント・スタイルタグの扱いが不完全** と複数報告されている。

### 1.4 rsvg-convert / librsvg

| 項目 | 内容 |
|---|---|
| 最新版 | librsvg 2.54+（Wikipedia/Wikimedia で 2025年3月時点採用） |
| macOS インストール | `brew install librsvg` |
| 日本語対応 | **macOS で既知の問題あり** |

**macOS での既知の問題**:
- librsvg は **fontconfig ベース**だが、macOS ネイティブは **CoreText ベース**。両者の統合は歴史的に不完全
- Hiragino Sans など **macOS 組み込みフォントが .ttc（コレクション）形式**で、fontconfig からは一部の weight しか見えないケース
- フォント追加時に **プロセス再起動が必要**（GNOME librsvg issue #536）
- Homebrew で `librsvg` を入れても、**別途 `font-noto-sans-cjk-jp` をインストール**しないと日本語が tofu（□□□）化するのが典型

**回避策**:
```bash
brew install --cask font-noto-sans-cjk-jp
# または
brew install --cask font-noto-sans-cjk
```
その上で SVG 内で `font-family="Noto Sans CJK JP"` を明示指定。

### 1.5 ImageMagick 7.x

| 項目 | 内容 |
|---|---|
| 日本語対応 | 可能だが **フォント明示指定必須** |
| SVG 対応 | 内部で librsvg/Inkscape/MSVG を呼び出し（ビルド依存） |

ImageMagick 7.x は `-font "NotoSansCJKjp-Regular"` 形式で明示指定すれば日本語描画可能だが、**内部 SVG デリゲートが librsvg の場合は 1.4 と同じ問題を継承**する。macOS では Inkscape デリゲート経由が安定。

### 1.6 Playwright / Puppeteer（ヘッドレスブラウザ）

| 項目 | 内容 |
|---|---|
| 日本語対応 | **ブラウザ内蔵フォントスタックに依存**、一般に良好 |
| SVG 描画品質 | **最高品質**（Chromium の SVG エンジン） |
| デメリット | 起動コスト大、依存重い、タイムアウト制御が必要 |

**Puppeteer 既知の注意点**:
- `setContent` → `screenshot` 間にタイムアウトを入れないと **SVG レンダ未完了でキャプチャ**される（puppeteer/puppeteer#791）
- カスタムフォント使用時は `@font-face` の CSS で埋め込む必要あり

**Playwright** は Chromium/Firefox/WebKit すべてドライブ可能。日本語中心の PDF/PNG 生成で **非ラテンフォントへの対応が Puppeteer より安定**と評される（Medium, Surasith Kaewvikkit）。

### 1.7 resvg / resvg-py / resvg-js（新潮流）

| 項目 | 内容 |
|---|---|
| 実装言語 | Rust（内部は tiny-skia） |
| Python バインディング | **resvg-py 0.2.6**（2026-01-14 リリース） |
| Node.js バインディング | **resvg-js**（@thx/resvg-js） |
| 最大の強み | **システムフォント非依存でクロスプラットフォーム再現性** |

**公式説明より**:
> "resvg doesn't rely on any system libraries, which allows reproducible results on all supported platforms—rendering the same SVG file on x86 Windows and ARM macOS produces identical images with each pixel having the same value."

**日本語フォント対応**:
- `font_dirs=["/path/to/fonts"]` で明示ロード必須
- `<text>` 要素は **1 つ以上フォントがロードされていないとパースされない**
- Noto Sans CJK JP を明示読み込みすれば macOS/Linux で同一描画

**例（resvg-py）**:
```python
import resvg_py
png_bytes = resvg_py.svg_to_bytes(
    svg_string=svg,
    font_dirs=["/Users/xxx/Library/Fonts"],
    default_font_family="Noto Sans CJK JP"
)
```

**パフォーマンス**:
- resvg-js ベンチ: 39.6 ops/s（sharp より 72% 高速、ただし SVG 内容依存）
- 逆に単純アイコン大量変換では sharp の方が 3 倍速いケースも報告あり（resvg-js issue #145）

### 1.8 Satori（Vercel）

| 項目 | 内容 |
|---|---|
| GitHub Stars | **約 12.9k**（2025-2026時点） |
| 実装 | TypeScript/JavaScript、HTML/CSS → SVG → PNG |
| Python 版 | **公式 Python 版は存在しない** |
| 日本語対応 | フォント明示ロードで完全対応（Noto Sans JP 利用例多数） |

Vercel の OG Image（`@vercel/og`）の内部エンジン。HTML+CSS を書ける開発者には最高の選択肢だが、**Python エコシステムからは直接使えない**（Node.js サブプロセス起動が必要）。

---

## 2. macOS での日本語フォント解決の落とし穴

### 2.1 fontconfig vs CoreText

| 項目 | fontconfig（Linux 起源） | CoreText（macOS ネイティブ） |
|---|---|---|
| macOS での状態 | Homebrew 経由で動作するが**完全統合ではない** |  macOS ネイティブ、Hiragino/游ゴシック等を完全認識 |
| 利用ツール | librsvg, cairo, cairosvg 等 | CoreGraphics, WebKit, Quartz |
| 日本語フォント | **明示追加必要**（Homebrew cask 等で） | **最初から利用可** |

**結論**: librsvg/cairosvg 系は fontconfig 依存のため、macOS で日本語を使うには **Noto Sans CJK JP 等を別途 Homebrew でインストール** し、fontconfig の cache を更新する必要がある。

### 2.2 librsvg で Hiragino が使えない問題（2025年時点）

- `Hiragino Sans.ttc` / `Hiragino Kaku Gothic ProN.otf` は macOS システムに存在
- しかし librsvg は **fontconfig 経由でしか見られない**
- macOS システムフォントディレクトリ `/System/Library/Fonts/` を fontconfig が読み取っても、**.ttc（TrueType Collection）の扱いが不安定**
- 結果: `font-family="Hiragino Sans"` と SVG に書いても **Sans（デフォルト）にフォールバック → tofu 化**

**実務的な対策**:
1. SVG に Noto Sans CJK JP を明示指定
2. Homebrew で `font-noto-sans-cjk-jp` をインストール
3. または librsvg を使わず Pillow 直接描画に切り替える（**最も確実**）

### 2.3 Homebrew でインストールされるフォント

Homebrew cask で提供される主要日本語フォント:

| Formula | フォント |
|---|---|
| `font-noto-sans-cjk` | Noto Sans CJK（全地域、巨大） |
| `font-noto-sans-cjk-jp` | Noto Sans CJK JP のみ（推奨） |
| `font-noto-serif-cjk-jp` | Noto Serif CJK JP |
| `font-noto-sans-mono-cjk-jp` | 等幅版 |

インストール先: `~/Library/Fonts/`（ユーザー）または `/Library/Fonts/`（システム）

Pillow から利用する際のパス例:
```python
font_path = "/Users/xxx/Library/Fonts/NotoSansCJKjp-Regular.otf"
# または Homebrew で入れた場合
font_path = "/opt/homebrew/share/fonts/NotoSansCJKjp-Regular.otf"
```

---

## 3. 直接 PNG 生成 vs SVG 中間形式の比較

### 3.1 Pillow 直接描画（ImageFont.truetype + ImageDraw）

**標準パターン**（Pillow 10.x 以降推奨）:
```python
from PIL import Image, ImageDraw, ImageFont

img = Image.new("RGB", (1080, 1080), (255, 255, 255))
draw = ImageDraw.Draw(img)
font = ImageFont.truetype("/path/to/NotoSansCJKjp-Bold.otf", size=72)

text = "保存必須\nサプリ3選"
# textbbox で正確なバウンディングボックスを取得（getsize は deprecated）
bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=20, align="center")
w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]

# 中央配置
draw.multiline_text(
    ((1080 - w) / 2, (1080 - h) / 2),
    text,
    font=font,
    fill=(30, 30, 30),
    spacing=20,
    align="center",
    anchor="la"  # TrueType font のみ
)
img.save("output.png")
```

**重要な API 変遷**:
- `font.getsize()` → **deprecated**（Pillow 9.2〜）
- `draw.textsize()` → **deprecated**
- `draw.textbbox()` / `draw.multiline_textbbox()` → **新推奨API**（Pillow 8.0〜、返り値は `(left, top, right, bottom)`）
- `font.getbbox()` / `font.getlength()` → 単一行の測定に使用
- `anchor` パラメータ → TrueType フォントのみ（`"la"`, `"mm"`, `"rs"` 等）

**数値の自動色分け・色アクセント付き描画**:
```python
import re

def draw_colored_text(draw, text, pos, font, default_color, accent_color):
    """数値を強調色で描画"""
    x, y = pos
    parts = re.split(r'(\d+(?:\.\d+)?)', text)
    for part in parts:
        color = accent_color if re.match(r'^\d', part) else default_color
        draw.text((x, y), part, font=font, fill=color)
        x += font.getlength(part)
```

**日本語の自動改行**:
- 標準 `textwrap` モジュールは **英単語前提**で日本語には不向き
- **BudouX**（Google 製、機械学習ベース）が推奨
  ```python
  import budoux
  parser = budoux.load_default_japanese_parser()
  phrases = parser.parse("今日は天気です。")  # ['今日は', '天気です。']
  ```
- BudouX は Chrome 119+ にも統合済み、npm/PyPI 両方提供

### 3.2 SVG → PNG 経由のアプローチ

**メリット**:
- テンプレート化が容易（デザイナーが SVG を直接編集できる）
- ベクター的なレイアウト調整が直感的
- ブラウザで事前プレビューできる

**デメリット**:
- **日本語フォント解決が変換ツールに依存**（最大の落とし穴）
- 変換ツールごとに SVG 仕様のカバー率が異なる
- デバッグが二段階になる（SVG レンダエラー vs 変換エラー）

### 3.3 比較表（本用途での評価）

| 観点 | Pillow 直接描画 | cairosvg | resvg-py | Playwright |
|---|---|---|---|---|
| 日本語品質 | ◎ Raqm経由で高品質 | × poorly supported | ◎ フォント明示で完全 | ◎ ブラウザ品質 |
| macOS での動作 | ◎ 問題なし | △ fontconfig 問題 | ◎ システム非依存 | ◎ 問題なし |
| パフォーマンス | ◎ 高速 | ○ 中 | ○ 中 | × 起動コスト大 |
| 依存の重さ | ◎ Pillowのみ | △ Cairo native | ○ Rust binary同梱 | × Chromium必須 |
| 保守性 | ◎ コード内完結 | ○ SVG分離可 | ○ SVG分離可 | △ CSS/HTML知識 |
| デバッグ容易性 | ◎ Python完結 | △ SVG+fontconfig | ○ ログ充実 | △ ブラウザログ |
| 再現性 | ◎ | △ システム依存 | ◎ ピクセル同一 | ○ ブラウザ依存 |
| テキスト中心画像 | **◎ 最適** | × 不向き | ○ 可 | ○ 可 |
| 複雑ベクター図 | △ 描画コード長く | ○ | ◎ | ◎ |

---

## 4. Production 環境での採用事例

### 4.1 日本での採用事例（Pillow）

- **Qiita / Zenn / note / はてなブログ**: Pillow 10.4.0 で日本語 1800 文字メタデータ埋め込み・画像生成の実装例多数（2024-2025）
- **株式会社一創 techblog**: Pillow による画像加工テクニックを採用事例として公開
- **ラクーンホールディングス techblog**: BudouX + 画像生成の組み合わせを紹介

### 4.2 Satori 系（Node.js エコシステム）

- **Vercel**: `@vercel/og` として公式提供、Next.js プロジェクトで広く採用
- **テラーノベル**: Satori による OGP 画像生成の本番事例（Zenn）
- **SvelteKit / Astro / Nuxt**: 各 SSG/SSR フレームワークで OGP 画像生成に採用

### 4.3 Canvas / sharp（Node.js）

- **node-canvas**: CJK フォント登録に **macOS/Windows プラットフォーム差**の issue 多数（#1674, #2285）
- **sharp**: SVG→PNG に resvg または librsvg を内部使用。日本語フォント解決は呼び出し元の責任

### 4.4 GitHub Star 数参考値（2025-2026）

| プロジェクト | Stars | 言語 |
|---|---|---|
| Pillow | 約 12k | Python |
| Vercel Satori | 約 12.9k | TypeScript |
| resvg (Rust 本体) | 約 3.5k | Rust |
| resvg-js | 約 1.1k | TS/Rust |
| cairosvg | 約 720 | Python |
| svglib | 約 830 | Python |
| BudouX | 約 3.3k | TS/Python/Java |

---

## 5. ベストプラクティス結論

### 5.1 本用途（macOS + Python + 日本語テキスト中心 + 1:1 PNG）の最推奨

**第1選択: Pillow 12.x 直接描画**

```python
# 推奨スタック
pillow >= 12.0.0
budoux >= 0.7.0  # 日本語自動改行
# フォント: Noto Sans CJK JP（無料、安定、商用可）
```

**理由**:
1. SVG 中間形式の fontconfig/librsvg 問題を**完全回避**
2. **依存が Pillow のみ**（pip install で完結、Rust/Cairo 等のネイティブ依存なし）
3. テキスト中心デザインでは **SVG の利点がほぼ無い**
4. `textbbox` + `multiline_text` で精密な中央配置が可能
5. BudouX との組み合わせで**日本語の自然な改行**を実現
6. macOS 上でも **Hiragino Sans .ttc を直接パス指定でロード可能**
7. 数値の色分け・アイコン挿入など**動的コンテンツ生成が Python コードで完結**

### 5.2 代替案の pros/cons

| スタック | Pros | Cons | 採用条件 |
|---|---|---|---|
| **resvg-py + Noto CJK JP** | ピクセル同一再現性、SVGテンプレート化 | Rust binary 同梱、SVG 編集知識必要 | デザイナー協業でテンプレ運用したい場合 |
| **Playwright + HTML/CSS** | 最高品質、Web技術で表現 | Chromium 依存、起動コスト、複雑 | 既に Web 資産がある、PDF/動画も扱う |
| **cairosvg** | Pure Python（Cairo除く） | 日本語 poorly supported | 使わない |
| **svglib** | Pure Python | 日本語不完全 | 使わない |
| **librsvg CLI** | 外部プロセスで軽量 | macOS で日本語 tofu 化頻発 | 使わない |
| **Satori (Node サブプロセス)** | HTML/CSS で書ける | Node.js 依存、Python 連携面倒 | フロントエンド知識が強い場合のみ |

### 5.3 2025-2026 年時点の主流

**データポイント**:
- **Pillow 12.0.0** が 2025-10-15 リリース、Python 3.14 対応、zlib-ng で PNG 圧縮高速化
- **resvg-py 0.2.6** が 2026-01-14 リリース、クロスプラットフォーム再現性を武器に普及中
- **Vercel Satori** は Node.js エコシステムで OGP 画像の事実上の標準
- **BudouX** は Chrome にも統合され、CJK 改行の標準ツールに

**日本の商用サービスの傾向**:
- **Python 系**: Pillow 直接描画が依然主流（Qiita/Zenn/note 記事の実装例が豊富）
- **Node.js 系**: Satori + resvg-js の組み合わせが新標準
- **エンタープライズ**: Playwright/Puppeteer で高品質画像生成

---

## 6. 実装推奨構成（本プロジェクト向け）

```python
# requirements.txt
Pillow>=12.0.0
budoux>=0.7.0

# フォント（いずれか）
# - macOS 組み込み: /System/Library/Fonts/ヒラギノ角ゴシック W6.ttc
# - Noto Sans CJK JP: Homebrew または手動DL
# - 源ノ角ゴシック (Source Han Sans): GitHub で配布
```

**サンプル実装**:
```python
from PIL import Image, ImageDraw, ImageFont
import budoux

# 設定
CANVAS_SIZE = (1080, 1080)
BG_COLOR = (255, 255, 255)
TEXT_COLOR = (30, 30, 30)
ACCENT_COLOR = (229, 57, 70)  # 数値強調色
FONT_PATH = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"  # macOS
# FONT_PATH = "~/Library/Fonts/NotoSansCJKjp-Bold.otf"  # Noto 派
FONT_SIZE = 80

# BudouX で日本語を phrase 単位に分割（折返し候補）
parser = budoux.load_default_japanese_parser()

def render_slide(text: str, output_path: str):
    img = Image.new("RGB", CANVAS_SIZE, BG_COLOR)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

    # 自動改行
    phrases = parser.parse(text)
    lines = []
    current = ""
    max_width = CANVAS_SIZE[0] - 160  # 左右 margin 80px
    for phrase in phrases:
        test = current + phrase
        if font.getlength(test) > max_width:
            lines.append(current)
            current = phrase
        else:
            current = test
    if current:
        lines.append(current)
    wrapped = "\n".join(lines)

    # 中央配置
    bbox = draw.multiline_textbbox((0, 0), wrapped, font=font, spacing=24, align="center")
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.multiline_text(
        ((CANVAS_SIZE[0] - w) / 2, (CANVAS_SIZE[1] - h) / 2),
        wrapped,
        font=font,
        fill=TEXT_COLOR,
        spacing=24,
        align="center",
        anchor="la"
    )
    img.save(output_path, "PNG", optimize=True)
```

---

## 7. 参考資料・ソース

### 公式ドキュメント
- [Pillow (PIL Fork) 12.2.0 documentation - ImageDraw](https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html)
- [Pillow (PIL Fork) 12.2.0 documentation - ImageFont](https://pillow.readthedocs.io/en/stable/reference/ImageFont.html)
- [Pillow 12.0.0 Release Notes (2025-10-15)](https://pillow.readthedocs.io/en/stable/releasenotes/12.0.0.html)
- [Pillow Text anchors documentation](https://pillow.readthedocs.io/en/stable/handbook/text-anchors.html)
- [CairoSVG Official Documentation](https://cairosvg.org/documentation/)
- [CairoSVG PyPI](https://pypi.org/project/CairoSVG/)
- [svglib PyPI](https://pypi.org/project/svglib/)
- [resvg-py documentation](https://resvg-py.readthedocs.io/)
- [resvg-py Fonts guide](https://resvg-py.readthedocs.io/en/latest/font.html)
- [resvg Rust crate](https://lib.rs/crates/resvg)
- [librsvg on Wikipedia](https://en.wikipedia.org/wiki/Librsvg)
- [librsvg — Homebrew Formulae](https://formulae.brew.sh/formula/librsvg)

### GitHub プロジェクト
- [Vercel Satori](https://github.com/vercel/satori) (約 12.9k stars)
- [resvg-js](https://github.com/thx/resvg-js)
- [satori-html](https://github.com/natemoo-re/satori-html)
- [Google BudouX](https://github.com/google/budoux)
- [Pillow](https://github.com/python-pillow/Pillow)
- [Pillow Font Fallback script](https://github.com/TrueMyst/PillowFontFallback)
- [notofonts/noto-cjk](https://github.com/notofonts/noto-cjk)

### 関連 Issue / 議論
- [sharp #2399: Rendering SVGs with custom fonts on macOS](https://github.com/lovell/sharp/issues/2399)
- [librsvg #536: text rendering requires restart to detect new fonts](https://gitlab.gnome.org/GNOME/librsvg/-/issues/536)
- [Pillow #8092: Rendering multi line text in bounding box](https://github.com/python-pillow/Pillow/issues/8092)
- [node-canvas #1674: Can't render Noto Sans CJK JP on Windows](https://github.com/Automattic/node-canvas/issues/1674)
- [puppeteer #791: Page.screenshot does not wait for SVG rendering](https://github.com/puppeteer/puppeteer/issues/791)
- [resvg-js #145: sharp is faster for mass SVG to PNG conversion](https://github.com/thx/resvg-js/issues/145)

### Homebrew フォント
- [font-noto-sans-cjk-jp](https://formulae.brew.sh/cask/font-noto-sans-cjk-jp)
- [font-noto-sans-cjk](https://formulae.brew.sh/cask/font-noto-sans-cjk)
- [font-noto-serif-cjk-jp](https://formulae.brew.sh/cask/font-noto-serif-cjk)

### 日本語技術ブログ
- [Satoriによる快適＆ハイパフォーマンスな画像生成！ (Zenn - テラーノベル)](https://zenn.dev/tellernovel_inc/articles/7a3966d2085c15)
- [Satori + SvelteKit で OGP 画像を自動生成する (azukiazusa.dev)](https://azukiazusa.dev/blog/satori-sveltekit-ogp-image/)
- [「BudouX」を使ってテキストの折り返しを自動化しよう！ (Raccoon Tech Blog)](https://techblog.raccoon.ne.jp/archives/1644901460.html)
- [Pythonでの画像生成: Pillowとランダムなパターンの作成](https://pythonjp.ikitai.net/entry/2023/12/31/224812)
- [Pillowを用いた主要な画像加工テクニック (株式会社一創)](https://www.issoh.co.jp/tech/details/1343/)

### 解説記事
- [How to Convert SVG to PNG in Python (Medium - Prasad Fernando)](https://medium.com/@prasadfernando90/how-to-convert-svg-to-png-in-python-4c655c59a571)
- [Generate Image From HTML Using Satori and Resvg (Anas Rin)](https://anasrin.dev/blog/generate-image-from-html-using-satori-and-resvg/)
- [Generate Image From HTML Using Satori and Resvg (DEV Community)](https://dev.to/anasrin/generate-image-from-html-using-satori-and-resvg-46j6)
- [Wrap and Render Multiline Text on Images Using Python's Pillow Library (DEV.to)](https://dev.to/emiloju/wrap-and-render-multiline-text-on-images-using-pythons-pillow-library-2ppp)
- [Drawing Text on Images with Pillow and Python (Mouse Vs Python)](https://blog.pythonlibrary.org/2021/02/02/drawing-text-on-images-with-pillow-and-python/)
- [Python Pillow: How to center align text horizontally (OneLinerHub)](https://onelinerhub.com/python-pillow/how-to-center-align-text-horizontally)
- [Convert SVG to PNG using Headless Chrome (imgix)](https://docs.imgix.com/en-US/getting-started/tutorials/developer-guides/convert-svg-to-png-using-headless-chrome)
- [Generate PDF (supporting Non-Latin fonts) with Puppeteer (Medium)](https://medium.com/@surasith_aof/generate-pdf-support-non-latin-fonts-with-puppeteer-d6ca6c982f1c)
- [Tofu: Why Characters Show as Empty Rectangles (SymbolFYI)](https://symbolfyi.com/guides/tofu-missing-glyphs/)

---

**調査実施日**: 2026-04-05
**主な情報源**: Pillow 公式ドキュメント、GitHub Issues、Homebrew Formulae、日本語技術ブログ（Zenn/Qiita/DEV Community）、Vercel 公式、Google 公式
