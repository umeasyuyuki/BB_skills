---
name: tiktok-fit-post-competitor-analysis
description: テーマごとに日本語投稿を単位として競合分析し、独自化ポイントを抽出するスキル。特定アカウント固定ではなく、都度の検索結果から伸びる型と不足情報を抽出したい時に使う。
---

# TikTok Fit Post Competitor Analysis

## 概要

入力テーマ単位で競合投稿を分析し、差別化に使える論点を返す。

## コマンド

- `/analyze-posts テーマ`
- `/analyze-posts-deep テーマ`
- `/analyze-cross-platforms テーマ`

## ルール

- アカウント固定ではなく投稿単位で調査
- 日本語投稿のみ
- 対象媒体は TikTok / YouTube / Instagram
- 競合の文面をコピーしない
- 視聴者実用性を最優先で差別化する

## 抽出項目

- フックの型
- 構成の型
- 主張の型
- 根拠提示の型
- 保存導線の型

## 必須出力

1. `競合投稿スナップショット`
2. `共通パターン`
3. `独自化アイデア`
4. `台本作成への指示`

出力はMarkdown。テンプレートは `references/post-analysis-template.md` を使う。
