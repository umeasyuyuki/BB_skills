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

- `sections.body`（投稿本文 500-700 字、L1-L4 全て含む完成形）
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

- `sections.body`（記事本文 2500-3500 字、L1-L4 含む完成形 + 脚注 5-8 件）
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

Threads → Note → LINE OC の動線で、各記事がどの段階に位置するかを記録する。

| 値 | 意味 | 該当媒体 |
|---|---|---|
| `awareness` | 認知段階（要点・抽象） | Threads |
| `engagement` | エンゲージメント段階（深掘り） | Note |
| `community` | コミュニティ段階（双方向） | （LINE OC、保存対象外） |

将来的に Threads → Note → LINE OC の遷移率を分析する際の軸として活用する。

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
