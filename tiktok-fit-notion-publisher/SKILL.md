---
name: tiktok-fit-notion-publisher
description: 調査・評価チェック・台本などの投稿ドキュメントをNotionデータベースへ保存するスキル。エンゲージメント指標は不要で、台本を含むレポートを自動保存したい時に使う。
---

# TikTok Fit Notion Publisher

## 概要

投稿コンテンツの成果物（調査・評価チェック・台本・総まとめ表・根拠）をNotionに格納する専用スキル。

## このスキルで扱うもの

- エンゲージメント分析は扱わない
- 保存対象は「作成済みドキュメント」
- 台本を含むレポートは自動保存対象

## データパッケージ形式

`references/document-package-template.json` を使用する。

必須キー:

- `title`
- `theme`
- `workflow`
- `content_type`（`carousel` / `note` / `x_post`）
- `status`
- `approved`
- `sections.title_suggestions`（★タイトル改善案5つ。必ず独立セクションとして格納する）
- `sections.research`
- `sections.compliance_check`
- `sections.script`
- `sections.caption`（★キャプション全文。3500字以上。carousel の場合は必須）
- `sections.summary_table`
- `sections.references`

## コマンド

- `/package-create` : ドキュメントから保存パッケージJSONを作成
- `/package-save-notion` : JSONをNotionへ保存
- `/notion-target` : 保存先Notion DB/Data Sourceを固定設定
- `/notion-publish` : 1コマンドで保存（JSON/Markdown対応、台本セクションは自動承認）
- `/notion-dry-run` : 保存前検証
- `/notion-save-json` : 単体保存
- `/notion-autosave-inbox` : inbox一括保存

## 依存スクリプト

- `scripts/create_document_package.py`
- `scripts/package_approval.py`
- `scripts/notion_target.py`
- `scripts/notion_publish.py`
- `scripts/notion_save_document.py`
- `scripts/notion_autosave.py`

## 設定優先順位

1. CLI引数（`--notion-data-source-id` など）
2. skill 配下の `.notion-target.json`（`/notion-target` で設定）
3. 環境変数（`NOTION_DATA_SOURCE_ID` / `NOTION_DATABASE_ID` / `NOTION_API_KEY`）

既定では current working directory の `.notion-target.json` ではなく、この skill 配下の `.notion-target.json` を参照する。
`notion_database_id` と `notion_data_source_id` が食い違う場合は、別DBへの誤保存を防ぐため保存を中止する。

## 台本スタイルメタデータの Notion 装飾変換

台本セクション（`sections.script`）のテキスト形式メタデータを、Notion のリッチテキスト装飾に変換して保存する。

### レイヤーヘッダーの解析

`メイン・大・赤` のようなレイヤーヘッダー行を検出し、次の行以降のテキストに装飾を適用する。

### 色のマッピング

| 台本の色指定 | Notion annotations.color |
|---|---|
| 赤 | `red` |
| 青 | `blue` |
| 黒 | デフォルト（color 指定なし） |

### サイズのマッピング

| 台本のサイズ | Notion ブロックタイプ / 装飾 |
|---|---|
| 大 | `heading_3` + `bold: true` |
| 中 | `paragraph`（通常テキスト） |
| 小 | `paragraph` + `color: "gray"` |

### レイヤーヘッダー自体の表示

`メイン・大・赤` のヘッダー行は Notion 上では **非表示にせず**、`color: "gray"` + `italic: true` で薄く表示する。台本の構造が確認できるようにするため。

### 感情設計ラベル

`感情設計: ラベル` の行は `callout` ブロック（emoji: 🎭）として保存する。

### content_type 別の保存ルール

| content_type | 保存する sections |
|---|---|
| `carousel` | title_suggestions, research, script（装飾変換あり）, caption, compliance_check, summary_table, references |
| `note` | title_suggestions, body（記事本文）, references |
| `x_post` | body（投稿本文）, references |

## 実行ルール

1. まず `package-create` でJSONを作る。
2. 台本セクションを含むレポートは自動でNotion保存する。
3. バッチ保存は `notion-autosave-inbox` を使う。
4. 出力は日本語Markdownで返す。

## 出力仕様

1. `保存対象サマリー`
2. `Notion保存結果`

## 参照

- `references/document-package-template.json`
- `references/notion-property-map-doc.json`
- `references/notion-setup.md`
