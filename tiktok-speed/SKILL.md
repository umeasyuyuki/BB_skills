---
name: tiktok-speed
description: TikTokカルーセル投稿を高速制作するClaude Code skill。ユーザーが `/Tiktok-speed`、`/tiktok-speed`、高速版、スピーディ版、GPTブラウザ版に貼る画像生成プロンプト、6〜7枚のTikTok投稿、タイトル案・台本・まとめ表・キャプション作成を求めた時に使う。Pillow、Driveアップロード、画像API生成は行わず、ChatGPTの画像生成Projectにコピペできるプロンプトまでを作る。
---

# TikTok Speed

## Overview

BB（Brain Bulking）向けTikTokカルーセルを短時間で作る入口専用skill。既存の重い `contents-fullmake` は残し、このskillでは「タイトル案、6〜7枚台本、GPT画像生成Project用プロンプト、Notion用まとめ表、キャプション」の5点だけを完成させる。

このskillでは画像を生成しない。Pillow、Driveアップロード、OpenAI Image API、Codex経由の画像生成は使わない。画像はユーザーがChatGPTブラウザ版の専用Projectにプロンプトを貼って手作業で生成する。

## Invocation

- `/Tiktok-speed テーマ`
- `/tiktok-speed テーマ`
- `/Tiktok-speed --auto テーマ`
- `/tiktok-speed --auto テーマ`

Claude Code環境でskill名が小文字のみ扱われる場合は `/tiktok-speed` を使う。ユーザーが `/Tiktok-speed` と書いた場合も、このskillとして扱う。

## Core Workflow

1. テーマを受け取る。テーマがない場合だけ1回質問する。
2. `references/workflow-spec.md` を読み、カテゴリ判定、最小リサーチ、タイトル、台本、キャプションの順に進める。
3. 文章トーンは `../contents-fullmake/references/writing-style.md` を参照して合わせる。
4. 出力形式は `references/output-spec.md` に厳密に合わせる。
5. 画像生成プロンプトは `references/image-prompt-spec.md` に合わせ、ChatGPT画像生成Projectにそのまま貼れる形で作る。
6. Notionへ保存する場合は `references/notion-publishing.md` のpackage構造に従う。
7. 最後に `references/quality-gates.md` を確認し、未達があれば修正してから完了する。

## Output Contract

最終出力は必ず次の5セクションだけにする。

1. `タイトル案`
2. `台本`
3. `画像生成プロンプト`
4. `まとめ表`
5. `キャプション`

補足、画像リンク、Drive保存結果、Pillow出力結果は出さない。必要な根拠リンクは `キャプション` の末尾かNotion保存用packageの `references` に入れる。

## Required Slide Structure

基本は7枚。テーマの論点が1つだけで薄い場合は4枚目または5枚目を省略して6枚にする。

1. 結論
2. 結論を説明する要素1
3. 2の補完
4. 結論を説明する要素2（あれば）
5. 4の補完（あれば）
6. まとめ・今日からできるアクション
7. コメント誘導

`chain_menu` カテゴリ（外食チェーン・コンビニの商品紹介）の場合は、◯選フォーマットでスライド構成が変わる。`references/chain-menu-spec.md` を参照する。

各スライドの画像指示は固定する。

- 上部: メインコピー
- 中部: 補足コピー
- 下部: 添付キャラクター

視聴者の目線が動かないよう、全スライドで文字位置、余白、キャラクター位置を統一させる。

## Categories

- `compare` A vs B、商品・成分・方法の比較
- `ingredient` 食品、サプリ、栄養素、成分解説
- `entertainment` 有名人、流行、固有名詞とフィットネス科学
- `debunk` 誤解、迷信、危険な常識の訂正
- `discovery` 意外な発見、保存したくなる知識整理
- `chain_menu` 特定外食チェーン or コンビニの実商品ラインナップから◯選で紹介

## References

- `references/workflow-spec.md`: 高速版の進行手順
- `references/output-spec.md`: 最終出力の正本
- `references/image-prompt-spec.md`: 毎回作る画像生成プロンプト仕様
- `references/chain-menu-spec.md`: chain_menuカテゴリ専用の構成・PFC・成分解説ルール
- `references/gpt-project-system-prompt.md`: ChatGPT Projectに貼る固定指示
- `references/notion-publishing.md`: Notion保存package仕様
- `references/quality-gates.md`: 完了前チェック
