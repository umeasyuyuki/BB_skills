---
name: tiktok-fit-slide-image-generator
description: 既存の台本Markdownから各スライド画像を一括生成するスキル。Antigravityで `/image @ファイル名またはパス` を実行し、nano banana運用向けにモデル指定を `pro` で固定して、1:1のミニマル図解画像を出力したい時に使う。
---

# TikTok Fit Slide Image Generator

## 概要

台本ファイルを読み取り、スライドごとに画像生成プロンプトを構築して一括生成する。

## コマンド

- `/image @ファイル名またはパス`

引数省略時は `data/pipeline/drafts/script.md` を使う。

## 出力

- 画像: `data/pipeline/images/<slug>/slide_XX.<ext>`
- プロンプト: `data/pipeline/images/<slug>/prompts/slide_XX.prompt.txt`
- 実行ログ: `data/pipeline/images/<slug>/manifest.json`

## 実行ルール

1. モデルは必ず `pro` を指定する。
2. 画像仕様は `references/nano-banana-system-prompt.md` を厳守する。
3. 人物が必要なスライドのみ `assets/kintaro-reference.jpg` を参照画像として添付する。
4. モードAはテキスト無改変、モードBは生物メカニズム系のみ平易化を許可する。
5. 失敗スライドがある場合は `manifest.json` に理由を記録する。

## 実行モード

- Antigravity運用（推奨、APIキー不要）
  - `python3 scripts/generate_slide_images.py --backend antigravity --input "<script>" --model pro`
  - 生成された `prompts/slide_XX.prompt.txt` を使い、Antigravityの画像生成機能で各ページ画像を作る。
- Antigravity運用（ルール撤廃テスト）
  - `python3 scripts/generate_slide_images.py --backend antigravity --input "<script>" --model pro --prompt-profile free`
  - ミニマル制約とモードA/B制約を外したテスト用プロンプトを作る。
- Gemini API運用（任意）
  - `python3 scripts/generate_slide_images.py --backend gemini --input "<script>" --model pro`
  - `GEMINI_API_KEY` が必要。

## スクリプト

- `scripts/generate_slide_images.py`

## 運用メモ

- Antigravity実行時は `/image @...` からこのスキルを呼び出す。
- APIキーなし運用は `--backend antigravity` を使う。

## 参照

- `references/nano-banana-system-prompt.md`
