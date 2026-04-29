---
name: bb-line-oc-morning
description: BB（Brain Bulking）LINE オープンチャット「サイエンスベースフィットネス」の毎朝発信用コンテンツを生成するスキル。Tips 3本＋ニュース4本の計7投稿を、LINE コピペ最適化フォーマット（おはようございます！＋箇条書き＋今日からできるアクション＋根拠リンク）で生成し、Notion「投稿管理」DB に保存。人間が朝に1本選んで投稿する半自動運用。
---

<!--
このファイルはコア手順のみ。詳細仕様は references/ 配下に分離。
上限: 250 行 / 12 KB（CONTRIBUTING.md 準拠）。
肥大化チェック: ../scripts/check_skill_size.sh bb-line-oc-morning を改修後に必ず実行。
-->

# BB LINE OC 毎朝発信オーケストレーター

## 概要

LINE オープンチャット「サイエンスベースフィットネス@Brain Bulking」の毎朝発信用コンテンツを、1コマンドで7投稿分生成して Notion に保存する。Threads/Note とは独立した「LINE OC 内向け、毎朝の場の温め」専用スキル。

人間が朝に Notion を開いて1本選び、コピペで LINE OC に投稿する運用を前提とする。

## 動線

```
研究/論文/規制ニュース/相場
   ↓
毎朝5:30 自動生成（cron）
   ↓
Notion「投稿管理」DB に7投稿保存
   ↓
人間が朝7時頃に1本選んで投稿、投稿済みチェックON
```

## 固定プロファイル

- 配信先: LINE オープンチャット「サイエンスベースフィットネス@Brain Bulking」
- 受信者: 既コミュニティメンバー（誘導 URL は**不要**）
- KPI: コミュニティ内のリアクション数・既読率・コメント率
- 文体: **標準語**で統一。BBトーン（断定・体言止め可）。AIっぽい曖昧表現禁止
- 出力: LINE コピペ用テキスト × 7（Tips 3 + News 4）
- 配信物: Tips（科学的根拠ベース）＋ News（直接系3＋間接系1）

## BB 思想（継承）

京大院生と薬剤師が、論文と法律で殴る。LINE OC は **場の温め + 日々の学び**で、読者の **行動変容** を起こす場。詳細: `bb-note-threads/SKILL.md` 「BBの思想」セクション参照。

## 起動フロー

| 呼び出し方 | 動作 |
|---|---|
| `/bb-line-oc-morning` | フルフロー実行（手動） |
| `/bb-line-oc-morning --dry-run` | Notion 保存をスキップして標準出力のみ |
| `/bb-line-oc-morning --skip-research` | 直近のリサーチ結果を再利用 |

cron 実行時（Phase B 自動運用時）は引数なしと同じ動作。

---

## Phase 0: 重複チェック前処理

サブステップ:

1. Notion「投稿管理」DB（data_source_id: `35171b5a-ad9a-80ce-b1a2-000b8947c6b9`）を query
2. 過去30日（`日付 ≥ 今日−30日`）のページを取得
3. 全タイトルを「重複候補リスト」として Phase 1 に渡す
4. 0件なら空リストを渡して継続

詳細: `references/workflow-spec.md` の「Phase 0」参照

---

## Phase 1: 並列リサーチ（3エージェント）

`TeamCreate({team_name: "bb-line-oc-research"})` でチームを作成し、以下3エージェントを並列起動する。

| name | 担当 | 出力本数 |
|---|---|---:|
| `tips-researcher` | Tips（PubMed / ACSM / NSCA / Examine.com / Reddit r/fitness） | 3 |
| `direct-news` | 直接ニュース（Google News：フィットネス・栄養・サプリ・規制） | 3 |
| `indirect-news` | 間接ニュース（Bloomberg / 日経ヘルスケア：原料相場・サプライチェーン・規制改正） | 1 |

各エージェントには **Phase 0 で取得した重複候補リスト**を渡し、類似テーマを除外させる。

ソース優先順位とクエリパターンの詳細: `references/source-priority.md`

調査エンジン: 第一選択 `gemini-3-pro-preview`、レート制限時は `gemini-2.5-pro`、それも失敗時は `codex exec`、最終手段で Claude WebSearch。

各エージェントは以下の構造で結果を返す（タイトル候補ごとに）:

```
## 候補N
- タイトル: <13〜30字、主張が一目で分かる>
- カテゴリ: tips | news-direct | news-indirect
- 要点: 3行（1行＝1事実、句点で終わる）
- アクション3本: <今日からできる具体行動>
- 一言コメント: <BBトーン1行>
- 根拠 URL: <実在確認済みのURL1〜2本>
- 重複判定: PASS（重複候補リストと類似度<70%）
```

---

## Phase 2: LINE フォーマッタ（7投稿一括生成）

3エージェントから返った計7候補を LINE コピペ最適化フォーマットに整形する。

### フォーマット骨格（全7投稿共通）

```
おはようございます！

[タイトル]

・[要点1]。
・[要点2]。
・[要点3]。

[一言コメント]。

▼今日からできるアクション
・[具体行動1]。
・[具体行動2]。
・[具体行動3]。

根拠：[URL]
```

詳細フォーマット仕様（先頭固定文・改行ルール・行数制限・絵文字/ハッシュタグ禁則）: `references/line-format-spec.md`

### アクション設計の必須要件

- 数字・量・タイミング込み（例「朝食時にホエイ20g」「就寝90分前に湯船15分」）、動詞ベース
- 今日中に実行できる範囲（特殊サプリ取り寄せ前提・高額機器前提はNG）
- 抽象語禁止（「意識する」「気をつける」「心がける」等は使わない）、1〜3個

---

## Phase 3: 薬機法簡易チェック

`tiktok-fit-compliance-check` の判定ルールを**簡易版**で適用する。LINE OC はクローズドコミュニティのため緩めだが、最低限の自衛として実施。

| 判定 | 対応 |
|---|---|
| Red（絶対NG表現を検出） | Phase 2 にフィードバックして書き直し（最大2回） |
| Yellow（要修正推奨） | 警告ログのみ、原文維持 |
| Green | そのまま Phase 4 へ |

絶対NG表現リストと安全な言い換え案: `references/compliance-light.md`

---

## Phase 4: Notion 保存（7ページ一括）

`mcp__notion__API-post-page` で直接7ページを並列作成（DB が3プロパティのみで軽量）。

| 保存先 | 値 |
|---|---|
| data_source_id | `35171b5a-ad9a-80ce-b1a2-000b8947c6b9` |
| プロパティ | 名前 / 日付（今日・JST）/ 投稿済みチェック=false |
| 本文 | カテゴリheading + LINEテキスト(code block) + メタ情報 |

詳細仕様（block 構造・カテゴリラベル・エラー時のリトライ）: `references/workflow-spec.md` の「Phase 4」参照

---

## セルフチェック（Phase 2 出力前必須）

8項目。1つでも不合格なら書き直し（最大2回）。

1. 先頭「おはようございます！」+ 空行
2. 句点（。）後で改行している
3. 箇条書き（・）が3要点 + 1〜3アクションで使われている
4. 絵文字・ハッシュタグが本文に混入していない（カテゴリheaderは Phase 4 のみ）
5. 「▼今日からできるアクション」セクション存在
6. アクションが具体（数字・量・タイミング込み）、抽象語なし
7. 根拠 URL が完成形（短縮なし）で末尾にある
8. タイトル13〜30字、重複候補リストと類似度<70%

---

## 自動実行（Phase B）

cron は `/schedule` スキル経由で登録する。初週は手動運用で品質を確認後、以下で cron 化:

```
schedule: "30 5 * * *"   # 毎朝 5:30 JST
command: /bb-line-oc-morning
timezone: Asia/Tokyo
```

cron 失敗時は ScheduleWakeup でリトライ、最終的にユーザーに通知。

---

## エラー時の挙動

| Phase | 失敗時の対応 |
|---|---|
| 0 | 重複候補なしで継続（警告ログ） |
| 1（1エージェント） | 該当カテゴリの本数を減らして継続 |
| 1（全失敗） | 中断、ユーザーに報告 |
| 2（セルフチェック2回連続不合格） | 手動修正待ちに格上げ |
| 3（Red 2回連続） | ユーザーに手動修正依頼 |
| 4（Notion 保存失敗） | `output/<YYYYMMDD>/` にバックアップ |

詳細: `references/workflow-spec.md`

## 他スキルとの分離

- **本スキル**: LINE OC **内向け** 毎朝発信、誘導 URL 不要
- **bb-note-threads**: Threads / Note 外向け、LINE OC へ誘導
- **contents-fullmake**: TikTok カルーセル、LINE OC URL **絶対NG**

---

## 参考ファイル

- `references/workflow-spec.md` — Phase 詳細・エージェント仕様・Notion API 呼び出し
- `references/line-format-spec.md` — LINE フォーマット仕様（改行・行数・禁則）
- `references/source-priority.md` — ソース優先順位とクエリパターン
- `references/compliance-light.md` — 薬機法簡易チェック（NG表現と言い換え）
