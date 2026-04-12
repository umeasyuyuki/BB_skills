---
name: tiktok-fit-slide-renderer
description: カルーセル台本Markdownから1:1 PNG画像（1080×1080）を生成するスキル。Pillowで直接描画、日本語自動改行、数値自動色分け対応。Windows/macOS/Linux完全互換（フォント同梱）。APIコストゼロ・ローカル完結。
---

# TikTok Fit Slide Renderer

## 概要

`tiktok-fit-carousel-script` が生成した台本Markdownを解析し、Pillowで**直接PNG画像を生成**するスキル。SVG中間形式を経由しないため、フォント解決の問題が発生しない。

**主な特徴**:
- 1:1 アスペクト比（1080×1080）の正方形PNG
- 日本語自動改行（BudouX使用）
- 数値＋単位を自動で青色化
- 出力は完全に決定論的（同じ入力→同じPNG）
- Noto Sans JP フォント同梱でOS非依存
- APIコストゼロ（ローカル処理）

## 前提条件

初回のみ:
```bash
cd tiktok-fit-slide-renderer
pip install -r requirements.txt
```

以上。Homebrew・ImageMagick等は不要。

## コマンド

- `/slide-render @ファイルパス` — 3フェーズを対話的に実行

## 3フェーズワークフロー

### Phase 1: パース（台本 → manifest.yaml）

```bash
python3 scripts/render_slides.py --parse --input <script.md>
```

台本MarkdownをYAMLマニフェストに変換し、スライド一覧とバリデーション警告を表示する。

### Phase 2: ユーザー編集 + バリデーション

生成されたYAML（`<slug>_render_manifest.yaml`）を直接編集 or Claude Code にチャットで修正依頼。

**編集可能な項目**:
- `text`: テキスト内容（`|` 記法で複数行）
- `size`: 大 / 中 / 小
- `color`: 黒 / 赤 / 青 または `#hex`
- `skip: true`: スライドを除外
- `canvas_override`: 個別のcanvas上書き

```bash
python3 scripts/render_slides.py --validate --manifest <manifest.yaml>
```

### Phase 3: 画像生成

```bash
python3 scripts/render_slides.py --render --manifest <manifest.yaml>
```

- 出力: `data/pipeline/images/<slug>/slide_NN.png`
- ログ: `data/pipeline/images/<slug>/manifest.json`

## Claude Code の動作ルール

### 基本ワークフロー

1. `--parse` を実行してYAMLマニフェストのパスを明示する
2. ユーザーに「テキストや色を修正しますか？」と確認する
3. ユーザーが編集を要求したらEditツールでYAMLを直接変更する
4. **ユーザーが明示的に承認するまで `--render` は実行しない**
5. `--render` 実行前に必ず `--validate` を通す

### 継続改善ルール（★重要）

ユーザーが調整指示を出したら、毎回以下を実行する:

1. 変更前の値を記録
2. Edit ツールで YAML or style_config.json を更新
3. **変更内容を feedback_log.jsonl に追記**:
   ```bash
   python3 scripts/render_slides.py --log --entry '{"slide":N,"field":"...","before":"...","after":"...","reason":"..."}'
   ```
4. ユーザーに変更完了を伝える

### レビュー提案タイミング

feedback_log.jsonl が10件を超えたら、自動で `analyze_feedback.py` の実行を提案する:

```bash
python3 scripts/analyze_feedback.py
```

パターン検出結果をユーザーに提示し、ルール化の可否を確認する。承認されたら:
- `style_config.json` を更新
- `references/learned_preferences.md` に履歴追記

## デザイントークン

`templates/style_config.json` で管理:

| 要素 | 値 |
|---|---|
| 大サイズ | 130pt / Black weight |
| 中サイズ | 80pt / Bold weight |
| 小サイズ | 44pt / Bold weight |
| 赤 | #E60012 |
| 青 | #1E40AF |
| 黒 | #1a1a1a |
| キャンバス | 1080×1080 / 余白80px |
| 数値自動色分け | ON（青色） |

## 台本フォーマット（入力）

`tiktok-fit-carousel-script` の新テキスト形式に対応:

```markdown
## スライド N（役割）

メイン・大・赤
テキスト行1
テキスト行2

サブ・中・黒
テキスト内容

補足・小・黒
テキスト内容

感情設計: ラベル
```

まとめ表スライドのみ、Markdown表形式を保持:

```markdown
## スライド N（まとめ表）

| 項目 | A | B |
|---|---|---|
| 比較軸1 | 値 | 値 |

感情設計: ラベル
```

## 出力仕様

- フォーマット: PNG
- サイズ: 1080×1080（1:1）
- 背景: #FFFFFF
- 出力先: `$BB_IMAGE_DIR/<slug>/slide_NN.png`（環境変数未設定時は `./output/投稿画像/<slug>/`）
- ログ: 出力先ディレクトリ内の `manifest.json`

### 画像出力先の設定

環境変数 `BB_IMAGE_DIR` で出力先を指定する。Git共有時に個人の絶対パスが混入しないための設計。

```bash
# 例: ~/.zshrc に追加
export BB_IMAGE_DIR="/Users/yourname/Brain Bulking/投稿画像"
```

未設定時はプロジェクト内の `./output/投稿画像/<slug>/` にフォールバックする。`--output-dir` フラグで都度上書きも可能。

## 参照

- `templates/style_config.json`: デザイントークン
- `scripts/render_slides.py`: メインスクリプト
- `scripts/analyze_feedback.py`: フィードバックパターン検出
- `fonts/NotoSansJP-VF.ttf`: 同梱フォント（SIL OFL）
- `references/learned_preferences.md`: ルール昇格履歴
