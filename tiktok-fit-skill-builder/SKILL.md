---
name: tiktok-fit-skill-builder
description: このアカウントのターゲット、文体、保存数重視方針を前提に、新しい運用スキルやワークフローを設計・追加するためのスキル。新カテゴリ追加、既存フロー改善、コマンド拡張、チェック工程追加を行いたい時に使う。
---

# TikTok Fit Skill Builder

## 概要

既存コンセプトを維持したまま、新しいskillやworkflowを増設する。

## アカウント固定コンテキスト

新規skill設計時は必ず次を継承する。

- KPI: 保存数
- 深掘り閾値: 保存率0.5%以上
- 対象: 20-40代男性、筋トレ中級以上
- 表現: 高校生レベル、日本語、専門語は噛み砕く
- 口調: フレンドリーかつロジカル、体言止め可
- 形式: フィード投稿（8-15枚）
- 文字制約: 1枚目13-20文字、2枚目以降30-50文字
- 既存カテゴリ比率: picks 30, myth 30, harms 20, intake 20
- 出力形式: Markdown

## コマンド

- `/skill-add skill名 目的`
- `/workflow-add workflow名 目的`
- `/command-add コマンド名 役割`
- `/skill-update skill名 変更内容`
- `/workflow-audit`

## 設計手順

1. 要件を短く定義
2. 既存skillへの統合か新設か判断
3. コマンド名と入出力を決定
4. ディレクトリ配置を決定する
   - TikTok投稿向けskill: `skills/tiktok/<skill-name>/`
   - note記事向けskill: `skills/note/<skill-name>/`
5. `SKILL.md` と `references` を作成
6. バリデーション実行

## 出力

1. `追加/変更の提案書`
2. `新コマンド仕様`
3. `必要ファイル一覧`
4. `実装後チェック項目`

## 参照

- `references/blueprint.md`
