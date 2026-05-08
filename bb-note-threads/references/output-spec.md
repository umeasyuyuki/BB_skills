# 出力仕様

各 Phase が生成する成果物のフォーマット定義。

## 全体パッケージ

bb-note-threads 完了時、オーケストレーターは以下のセクションを含む統合パッケージを構築する:

| # | セクション名 | Phase | 必須 |
|---|---|---|---|
| 1 | `title_input` | Phase 0 | ✅ |
| 2 | `category` | Phase 0 | ✅ |
| 3 | `research_merged` | Phase 1 | ✅ |
| 4 | `competitor_analysis` | Phase 1 | ⚠️（`--no-competitor` 時は省略） |
| 5 | `threads_post` | Phase 2 | ✅ |
| 6 | `note_article` | Phase 2 | ✅ |
| 7 | `compliance_threads` | Phase 3 | ✅ |
| 8 | `compliance_note` | Phase 3 | ✅ |
| 9 | `notion_threads_url` | Phase 4 | ✅ |
| 10 | `notion_note_url` | Phase 4 | ✅ |
| 11 | `note_com_draft` | Phase 5 | ✅（note-mcp 利用可能時） |

1〜8 が揃わない場合は Phase 4（Notion 保存）に進めない。Phase 5 は note-mcp が利用可能な環境でのみ実行する。

---

## Phase 2 出力詳細

### Threads 投稿（`threads_post`、ツリー構成、8 型）

Threads は **親ポスト + リプライ複数** のツリー構造で出力する。**本体ポストは 200-300 字、最終リプ（D-2 二段構成）は 240-300 字**。全文を低温の標準語で書き、専門用語は日常語に翻訳する。

**型別ツリー深さ（8 型）**:

| 型 | 親 | 本体リプ | 最終リプ | 合計 |
|---|---:|---:|---:|---:|
| ⚪選系 / ランキング系 / データ型 / 問いかけ型（3 構成版） | 1 | 1 | 1 | 3 |
| 体験談型 / 対比型 / 結論逆張り型 / ストーリー型 / 問いかけ型（4 構成版） | 1 | 2 | 1 | 4 |

**フォーマット**:

```markdown
# Threads 投稿（ツリー構成）

型: {⚪選系 / ランキング系 / 体験談型 / 対比型 / データ型 / 結論逆張り型 / 問いかけ型 / ストーリー型}

## 型選択メモ
- 採用案: {採用した型} — 理由: {1 行}
- 不採用案: {検討した別の型} — 理由: {1 行}

## 親ポスト（200-300 字）
{親ポスト本文}
字数: {N}字 / 1 行目誰向け明示: ✅ / 末尾の引き: 「{末尾フック}」

---

## 本体リプ 1（200-300 字）
{本体リプ 1 本文}
字数: {N}字 / 末尾の引き: 「{末尾フック}」または結論言い切り

---

## 本体リプ 2（200-300 字、4 構成版のみ）
{本体リプ 2 本文}
字数: {N}字 / 結論: 言い切り ✅

---

## 最終リプ（240-300 字、D-2 二段構成）
{Note 案内（メイン）+ 区切り + LINE OC 匂わせ（サブ）+ Note URL プレースホルダ}

字数: {N}字
構造: Note 案内（メイン）+ LINE OC 匂わせ（サブ）✅
区切り: `ーーー` または空行 2 行 ✅
Note URL プレースホルダ: 配置済み ✅
LINE 直 URL なし: ✅
専門用語翻訳済み: ✅

---
title_input: {投入タイトル}
カテゴリ: {category}
ツリー深さ: {N} ポスト
専門用語翻訳チェック: 全箇所翻訳済み ✅
セルフチェック結果: 全項目クリア
```

**最終リプ構造（D-2 二段構成、全型共通）**:

```
（メイン：Note 案内 100-150 字）
この投稿だけだと説明しきれない部分が多いので、詳しい根拠はNoteに置いておきます。

気になるところだけ読んでもらえれば大丈夫です。

📝 詳しい解説はこちら
【★Note URL を貼る★】

ーーー

（サブ：LINE OC 匂わせ 100-150 字）
「これ食べていい？」「サプリいる？」
みたいな体づくりの疑問を、
プロフィールの相談室でゆる〜く議論しています。

見るだけ参加も大歓迎です。
```

### Note 記事（`note_article`）

**note.com コピペ最適化規約（A 案、★必須）**:

- 各論理段落は **1 行で完結**。paragraph 内で `\n` 改行を使わない（読みやすさのための改行は空行で表現）
- 見出しは `## ` (H2) と `### ` (H3) のみ使用、H4 以下は使わない
- 導入直後に `[TOC]` を単独行で置く。note.com 側で H2/H3 から目次を自動生成する
- 自動 bold ルール: 数字＋単位、固有名詞、キー結論一文を `**...**` で囲んで出力（詳細は `note-style.md`）
- 区切り線は `────────` または `---`、引用は `> ` を使用
- Phase 4 で `scripts/md_to_notion_blocks.py` が markdown → Notion blocks に変換する
- Phase 5 で note.com に保存する前に、末尾の管理メタ情報とセルフチェック結果は削除する

**フォーマット**:

```markdown
# {タイトル}

{導入：手紙トーン}

{結論先出し}

[TOC]

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

## 関連リンク

ここまで読んでくれてありがとうございます。

BBでは、フィットネス・栄養・ヘルスケアの話を、NoteやSNSで少しずつ整理しています。

「これ食べていい？」「サプリいる？」みたいな体づくりの疑問を、オープンチャット「サイエンスベースフィットネス@Brain Bulking」でゆるく議論しています。

見るだけ参加も大歓迎です。

[オープンチャットに参加する](https://line.me/ti/g2/lmmjCh0V39BIgClQxQmsm4Hb-G8Hb7VFsnVOuw?utm_source=invitation&utm_medium=link_copy&utm_campaign=default)

※ 個別の医療相談や診断をする場所ではありません。

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
関連リンク案内: 配置済み（LINE OC 実リンク・医療相談免責 含む）
専門用語翻訳チェック: 全箇所翻訳済み（学術略称・カタカナ専門語・単位）✅
セルフチェック結果: 全項目クリア
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

## Phase 5 出力詳細

### note.com 下書き保存後の出力

```markdown
# note.com 下書き保存完了

article_key: {n...}
preview_url: {URL}
Notion Note ページ: {URL}
目次: `[TOC]` により自動生成対象
公開状態: 下書き（未公開）

## 次の確認ポイント

- 目次が導入直後に表示されているか
- H2/H3 の階層が崩れていないか
- 脚注と関連リンクが本文末尾に残っているか
- 誇大表現や薬機法上の違和感がないか
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
