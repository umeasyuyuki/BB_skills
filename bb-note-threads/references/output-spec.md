# 出力仕様

各 Phase が生成する成果物のフォーマット定義。

## 全体パッケージ

bb-note-threads 完了時、オーケストレーターは以下のセクションを含む統合パッケージを構築する:

| # | セクション名 | Phase | 必須 |
|---|---|---|---|
| 1 | `title_input` | Phase 0 | ✅ |
| 2 | `category` | Phase 0 | ✅ |
| 3 | `research_merged` | Phase 1 | ✅ |
| 4 | `differentiation_axes` | Phase 1 | ✅（researcher 出力に統合） |
| 5 | `threads_post` | Phase 2 | ✅ |
| 6 | `note_article` | Phase 2 | ✅ |
| 7 | `compliance_threads` | Phase 3 | ✅ |
| 8 | `compliance_note` | Phase 3 | ✅ |
| 9 | `notion_threads_url` | Phase 4 | ✅ |
| 10 | `notion_note_url` | Phase 4 | ✅ |

各セクションが揃わない場合は、Phase 4（Notion 保存）に進めない。

---

## Phase 2 出力詳細

### Threads 投稿（`threads_post`、ツリー構成）

Threads は **親ポスト + リプライ複数** のツリー構造で出力する。各ポスト 200-300 字。

**型別ツリー深さ**:

| 型 | 親 | 本体リプ | 誘導リプ | 合計 |
|---|---:|---:|---:|---:|
| ⚪選系 / ランキング系 | 1 | 1 | 1 | 3 |
| 体験談型 / 対比型 | 1 | 2 | 1 | 4 |

**フォーマット**:

```markdown
# Threads 投稿（ツリー構成）

型: {⚪選系 / ランキング系 / 体験談型 / 対比型}

## 親ポスト（200-300 字）
{親ポスト本文}
字数: {N}字 / 1 行目誰向け明示: ✅ / 末尾の引き: 「{末尾フック}」

---

## 本体リプ 1（200-300 字）
{本体リプ 1 本文}
字数: {N}字 / 末尾の引き: 「{末尾フック}」または結論言い切り

---

## 本体リプ 2（200-300 字、体験談型・対比型のみ）
{本体リプ 2 本文}
字数: {N}字 / 結論: 言い切り ✅

---

## 誘導リプ（200-300 字、最終ポスト）
{誘導リプ本文・L1 + L2-L4 固定文 + Note URL + LINE OC URL}
字数: {N}字
LINE OC URL: 直書き ✅
Note URL プレースホルダ: 配置済み ✅
チャット名「サイエンスベースフィットネス@Brain Bulking」: 末尾明記 ✅

---
title_input: {投入タイトル}
カテゴリ: {category}
ツリー深さ: {N} ポスト
L1 フック内容: {1 行で要約}
セルフチェック結果: 12/12 項目クリア
```

**誘導リプ構造（最終ポスト、共通）**:

```
{L1: テーマ連動フック、80-120 字に圧縮}

京大院生と薬剤師が、日本最先端を本気で目指す、
完全無料のフィットネス × ヘルスケアコミュニティ。

成分表を見て、体に必要なものを判断できるように。
毎朝、最新ニュースを翻訳して配信中 ↓
https://line.me/ti/g2/lmmjCh0V39BIgClQxQmsm4Hb-G8Hb7VFsnVOuw

📝 詳しい根拠と数値はこちら
【★Note URL を貼る★】

サイエンスベースフィットネス@Brain Bulking
```

### Note 記事（`note_article`）

**note.com コピペ最適化規約（A 案、★必須）**:

- 各論理段落は **1 行で完結**。paragraph 内で `\n` 改行を使わない（読みやすさのための改行は空行で表現）
- 見出しは `## ` (H2) と `### ` (H3) のみ使用、H4 以下は使わない
- 自動 bold ルール: 数字＋単位、固有名詞、キー結論一文を `**...**` で囲んで出力（詳細は `note-style.md`）
- 区切り線は `────────` または `---`、引用は `> ` を使用
- Phase 4 で `scripts/md_to_notion_blocks.py` が markdown → Notion blocks に変換する

**フォーマット**:

```markdown
# {タイトル}

{導入：手紙トーン}

{結論先出し}

## {本論セクション 1}
{本文}

## {本論セクション 2}
{本文}

## {本論セクション 3-5}
{本文}

{具体例・体験談}

## まとめ
{結論再確認}

────────

## もっと深く知りたいなら

{L1: テーマ連動フック、2-3 行に肉付け}

京大院生と薬剤師が、日本最先端を本気で目指す、
完全無料のフィットネス × ヘルスケア LINE コミュニティ。

毎朝、論文・市場・規制のトレンドを翻訳して配信。
読んでいるだけで、成分表を見て体に必要なものを
自分で判断できるレベルになる。

入っていることがステータスになる場所を、本気で作ってる。

→ https://line.me/ti/g2/lmmjCh0V39BIgClQxQmsm4Hb-G8Hb7VFsnVOuw
「サイエンスベースフィットネス@Brain Bulking」

## 脚注

[1] PubMed ID: ...
[2] ...
（5-8 件）

---
title_input: {投入タイトル}
文字数: {N}字（目標 2500-3500）
カテゴリ: {category}
セクション数: {N}
脚注数: {N}件（うち PubMed: {N}件）
LINE OC URL: 末尾セクションに直書き済み
セルフチェック結果: 12/12 項目クリア
```

---

## Phase 3 出力詳細

### compliance_threads / compliance_note

**フォーマット**:

```markdown
# 薬機法チェック結果（{Threads or Note}）

判定: Green / Yellow / Red

## 違反箇所（Red / Yellow のみ）

[1] 該当箇所: "{違反テキスト}"
    違反タイプ: 効能効果の暗示 / 治療効果の標榜 / 等
    重大度: 高 / 中 / 低
    修正提案: "{言い換え案}"

[2] ...

## 修正リトライ履歴

リトライ回数: {N}/2
最終判定: {Green / Yellow / Red}
```

---

## Phase 4 出力詳細

### Notion 保存後の出力

```markdown
# Notion 保存完了

Threads ページ: {URL}
Note ページ: {URL}
paired_post_url 相互リンク: 設定済み

## プロパティ確認

Threads:
  - content_type: threads
  - pricing_mode: free
  - funnel_stage: awareness
  - paired_post_url: {Note URL}

Note:
  - content_type: note
  - pricing_mode: free
  - funnel_stage: engagement
  - paired_post_url: {Threads URL}
```

---

## バックアップ出力（エラー時 or 任意保存時）

Phase 4 で Notion 保存に失敗した場合、または `--save-local` フラグ指定時、以下を `output/<YYYY-MM-DD-HHMM>/` に保存する:

```
output/<timestamp>/
├── 00_meta.json              # title_input, category, timestamps, errors
├── 01_research_merged.md     # Phase 1 マージ結果
├── 02_threads.md             # Phase 2 Threads 出力
├── 03_note.md                # Phase 2 Note 出力
├── 04_compliance.md          # Phase 3 両媒体チェック結果
└── 05_notion_pages.json      # Phase 4 保存先 URL（成功時）
```

環境変数 `BB_NOTE_THREADS_OUTPUT_DIR` で出力先を上書き可能。
