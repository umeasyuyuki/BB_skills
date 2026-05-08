# Notion 保存ルール

`tiktok-fit-notion-publisher` を使い、Threads と Note の 2 ページを **同一 DB・別ページ** として保存し、`paired_post_url` プロパティで相互リンクを張る。

`content_type` プロパティで `threads` / `note` をフィルタリング可能。TikTok カルーセルとは `content_type` で完全に分離される。

## 共通ルール

- 最終成果物は毎回 `tiktok-fit-notion-publisher` に渡して即時保存する
- `workflow` はこのスキルで判定したカテゴリ（compare / ingredient / entertainment / debunk / discovery）をそのまま引き継ぐ
- 保存に必要な項目が欠けている場合のみ、欠損項目を補ってから保存する
- 保存後、両ページに `paired_post_url` で相互リンクを書き込む

## ページ構成

| ページ | content_type | 含むセクション | funnel_stage |
|---|---|---|---|
| Threads 投稿 | `threads` | `body`, `references` | `awareness` |
| Note 記事 | `note` | `body`, `references` | `engagement` |

---

## Threads 投稿（content_type: threads）

### 必須セクション

- `sections.body`（投稿本文 500-700 字、最終リプの Note 案内まで含む完成形）
- `sections.references`（根拠リンク 3-5 件）

### 必須プロパティ

| プロパティ | 値 |
|---|---|
| `名前` (title) | 投入されたタイトルそのまま |
| `content_type` (select) | `threads` |
| `pricing_mode` (select) | `free` |
| `funnel_stage` (select) | `awareness` |
| `paired_post_url` (url) | Note ページの URL（Note 保存後に書き込む） |
| `Workflow` (select) | カテゴリ（compare / ingredient / entertainment / debunk / discovery） |
| `Status` (status) | `Draft` |
| `Approved` (checkbox) | `false` |
| `Created At` (date) | 保存時のタイムスタンプ |

---

## Note 記事（content_type: note）

### 必須セクション

- `sections.body`（記事本文 2500-3500 字、関連リンク案内 + 脚注 5-8 件）
- `sections.references`（根拠リンク 5-8 件、PubMed ID 必須含む）

### 必須プロパティ

| プロパティ | 値 |
|---|---|
| `名前` (title) | 投入されたタイトルそのまま |
| `content_type` (select) | `note` |
| `pricing_mode` (select) | `free`（将来 `paid` に切り替え） |
| `funnel_stage` (select) | `engagement` |
| `paired_post_url` (url) | Threads ページの URL（Threads 保存後に書き込む） |
| `Workflow` (select) | カテゴリ |
| `Status` (status) | `Draft` |
| `Approved` (checkbox) | `false` |
| `Created At` (date) | 保存時のタイムスタンプ |

---

## paired_post_url 相互リンク手順

```
Step 1: Threads ページを保存 → URL_T を取得
Step 2: Note ページを保存 → URL_N を取得
Step 3: Threads ページの paired_post_url プロパティに URL_N を書き込み
Step 4: Note ページの paired_post_url プロパティに URL_T を書き込み
```

書き込み API:
- `mcp__notion__API-patch-page` を使用
- `properties: { paired_post_url: { url: "..." } }` で更新

---

## pricing_mode の運用

将来的な Note 有料化（Threads 500 フォロワー後）に備えた土台。

| 値 | 意味 | 現在の運用 |
|---|---|---|
| `free` | 無料公開 | 全 Note 記事のデフォルト |
| `paid` | 有料公開 | Threads 500 フォロワー到達後に切り替え予定 |

**スキル本体では `free` のみセット**。`paid` への切り替えロジックは別タスクで実装する（今は土台のみ）。

---

## funnel_stage の運用

Threads → Note → LINE オープンチャットの動線で、各記事がどの段階に位置するかを記録する。

| 値 | 意味 | 該当媒体 |
|---|---|---|
| `awareness` | 認知段階（要点・抽象） | Threads |
| `engagement` | エンゲージメント段階（深掘り） | Note |
| `community` | コミュニティ段階（双方向） | （LINE オープンチャット案内、保存対象外） |

将来的に Threads → Note → LINE オープンチャットの遷移率を分析する際の軸として活用する。

---

## 保存スキーマ（document-package-template.json への入力）

```json
{
  "title_input": "プロテイン値上げで起きる栄養格差",
  "category": "ingredient",
  "pages": [
    {
      "content_type": "threads",
      "title": "プロテイン値上げで起きる栄養格差",
      "properties": {
        "pricing_mode": "free",
        "funnel_stage": "awareness",
        "Workflow": "ingredient",
        "Status": "Draft",
        "Approved": false
      },
      "sections": {
        "body": "{Threads 投稿本文 500-700 字}",
        "references": [
          {"label": "PubMed ID 12345", "url": "https://..."},
          {"label": "NZ MPI Q3 Report", "url": "https://..."}
        ]
      }
    },
    {
      "content_type": "note",
      "title": "プロテイン値上げで起きる栄養格差",
      "properties": {
        "pricing_mode": "free",
        "funnel_stage": "engagement",
        "Workflow": "ingredient",
        "Status": "Draft",
        "Approved": false
      },
      "sections": {
        "body": "{Note 記事本文 2500-3500 字 + 脚注}",
        "references": [
          {"label": "PubMed ID 12345", "url": "https://..."},
          {"label": "PubMed ID 67890", "url": "https://..."}
        ]
      }
    }
  ]
}
```

---

## エラー処理

| エラー | 対処 |
|---|---|
| Threads 保存失敗 | リトライ 1 回 → 失敗時は中断、ローカルバックアップ |
| Note 保存失敗（Threads は成功済み） | リトライ 1 回 → 失敗時は Note のみローカルバックアップ。Threads ページに `paired_post_url` を書けないため、Note 復旧後に手動で相互リンクを張る |
| paired_post_url 書き込み失敗 | リトライ 2 回 → 失敗時はユーザーに通知し、手動で書き込みを依頼 |
| 必須プロパティ欠落 | 中断、補完して再保存 |

---

## 過去データとの互換性

contents-fullmake が以前生成した `content_type: x_post` のページは、過去データとして触らない。新規データは bb-note-threads から `content_type: threads` で保存する。`x_post` を `threads` にリネームしない（過去データ保護）。

---

## note.com コピペ最適化のためのブロック変換規則（Note 専用、A 案）

Note ページを Notion → note.com にコピペした際、見出し・段落・箇条書き・太字を保持するため、Phase 4 の Markdown → Notion blocks 変換は以下のルールで行う。Threads ページは対象外（既存仕様維持）。

詳細な writer 側の出力規約は `note-style.md` の「note.com コピペ最適化（A 案）」を参照。

### Markdown → Notion blocks マッピング

| Markdown | Notion ブロック | 備考 |
|---|---|---|
| `# タイトル`（H1） | （body には入れない） | Notion ページの `投稿の原稿` (title) プロパティに設定 |
| `## 見出し` | `heading_2` | note.com の「大見出し」に対応 |
| `### 中見出し` | `heading_3` | note.com の「中見出し」に対応 |
| 通常段落（1 行で完結） | `paragraph` | `\n` を含まない 1 行を 1 ブロック |
| 空行 | （ブロック区切り） | paragraph ブロックの境界として機能 |
| `- 項目` | `bulleted_list_item` | 1 行 = 1 ブロック |
| `> 引用` | `quote` | 連続行は 1 つの quote にまとめる |
| `────────` または `---` | `divider` | 水平線 |
| `**強調**` | rich_text の `annotations.bold = true` | 段落・見出し・箇条書きすべての rich_text に適用 |

### rich_text 構築ルール

paragraph / heading / bulleted_list_item の `rich_text` 配列は以下の規則で構築する:

- `**太字**` の前後を分割し、太字部分には `annotations: {"bold": true}` を付ける
- 太字以外のセグメントは annotations なしのプレーンテキスト
- 1 segment あたり最大 1900 文字（Notion API の 2000 char 上限に対する安全マージン）
- segment 数の上限は実質ない（Notion API 側で 100 segments まで許容）

例: `「**1.5g/kg**」という条件である。**70kg** の男性なら **105g**。`

→
```json
{
  "type": "paragraph",
  "paragraph": {
    "rich_text": [
      {"type": "text", "text": {"content": "「"}},
      {"type": "text", "text": {"content": "1.5g/kg"}, "annotations": {"bold": true}},
      {"type": "text", "text": {"content": "」という条件である。"}},
      {"type": "text", "text": {"content": "70kg"}, "annotations": {"bold": true}},
      {"type": "text", "text": {"content": " の男性なら "}},
      {"type": "text", "text": {"content": "105g"}, "annotations": {"bold": true}},
      {"type": "text", "text": {"content": "。"}}
    ]
  }
}
```

### 変換スクリプト

リファレンス実装は `scripts/md_to_notion_blocks.py` に置く。Phase 4 で Notion 保存する前に、03_note.md → blocks JSON に変換して `mcp__notion__API-post-page` の `children` に渡す流れ。

呼び出し例:
```bash
python3 bb-note-threads/scripts/md_to_notion_blocks.py output/<ts>/03_note.md > /tmp/note_blocks.json
```

### 「note.com 想定」の見出しランクガイド

writer は以下の対応で見出しを書く:

- `## 結論` / `## 本論セクション名` / `## まとめ` / `## 関連リンク` / `## 脚注` → 大見出し（H2）
- 長い本論セクション内のサブ区切り（`### 軽量帯` / `### 中量帯` / `### 重量帯` 等）→ 中見出し（H3）

Threads セクションには見出しを使わず、平段落で構成する（既存仕様維持）。
