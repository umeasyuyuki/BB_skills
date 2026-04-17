---
name: contents-fullmake
description: テーマ1つで「TikTokカルーセル台本+画像、Note記事、X投稿」の3メディアを一気通貫生成。BB（筋トレ情報）アカウント専用。リサーチ・競合分析・タイトル評価・薬機法チェック・Notion保存まで自動。
---

<!--
このファイルはコア手順のみ。詳細仕様は references/ 配下に分離。
上限: 250 行 / 10KB（CONTRIBUTING.md 参照）。
1改修ごとに +30 行を超える追加は references/ への切り出しを検討すること。
肥大化チェック: ../scripts/check_skill_size.sh を改修後に必ず実行。
-->

# Contents Fullmake

## 概要

入口専用スキル。テーマを受け取り、カテゴリ判定 → 調査 → タイトル評価 → 3メディア生成 → 薬機法チェック → Notion 保存 → カルーセル画像生成までを担当する。Phase 1 はエージェントチームで並列実行する。

## 固定プロファイル

- KPI: 保存数、コメント数（ニーズ収集）
- コンセプト: 筋トレ中・上級者向け。コンディショニングや努力を最大化するための栄養学・サプリ情報。情弱ビジネスを終わらせる側
- 深掘り基準: 保存率 0.5% 以上
- 対象: 20-40 代男性、筋トレ中級以上
- 文章レベル: 高校生が理解できる日本語
- 口調: 情熱が見える怒り。事実で殴り、思想を叫ぶ。フレンドリーさより "本気さ"。体言止め可
- 形式: 画像カルーセル投稿（9〜12 枚可変、discovery のみ 10 枚固定）
- 出力: Markdown

## BB の思想

- 敵: 「知らない」につけ込んで金を抜く奴ら全員
- 信念: 正しい情報はタダで届けられる。俺らが証明する
- 姿勢: 京大の研究者と薬剤師が、論文と法律で殴る
- 宣言: 「情弱ビジネスを、終わらせる。」

## 起動フロー

引数の数で分岐する。詳細な判定ロジックは `references/category-router.md` 参照。

| 呼び出し方 | 動作 |
|---|---|
| `/contents-fullmake` | 対話モード：カテゴリ選択 → テーマ質問 → フルフロー |
| `/contents-fullmake テーマ` | **Phase 0 自動判定** → 信頼度 80% 以上で即実行、未満なら候補トップ2を信頼度付きでユーザー提示 → 選択 → フルフロー |
| `/contents-fullmake カテゴリ テーマ` | 直接指定（従来）→ フルフロー |

カテゴリは 5 種：compare / ingredient / entertainment / debunk / discovery（詳細は `references/workflow-spec.md`）

## Phase 0: カテゴリ自動判定（引数1個パターンのみ）

オーケストレーター自身がテーマ文字列からカテゴリを判定する（エージェント起動不要）。信頼度 ≥ 80% で即実行、< 80% なら候補トップ2をユーザー提示 → 選択待ち。判定精度は Notion `title_candidates` に記録し定期レビューする。

詳細（シグナルルール・信頼度計算・提示フォーマット・運用ログ）は `references/category-router.md` 参照。

---

## Phase 1: 並列チーム（research + competitor-analysis）

`TeamCreate({team_name: "contents-fullmake-team"})` でチームを作成し、以下 2 エージェントを `team_name` 指定で同時起動する。`SendMessage` による双方向通信を有効化する。

| name | 担当スキル | 役割 |
|---|---|---|
| `researcher` | `tiktok-fit-research` | 科学的根拠・PubMed・公式データの収集 |
| `competitor-analyst` | `tiktok-fit-post-competitor-analysis` | TikTok/YouTube/Instagram の競合投稿分析 |

通信ルール:

1. **researcher → competitor-analyst**（早期共有）: 調査序盤で「主要キーワード」「発見した切り口」を `SendMessage({to: "competitor-analyst"})` で共有。競合分析側は既存投稿が未カバーの独自角度を優先探索
2. **competitor-analyst → researcher**（差別化リクエスト）: 盲点発見時に `SendMessage({to: "researcher"})` で追加調査依頼。リサーチャーはエビデンスを補強
3. **合流**: 両エージェント完了後、オーケストレーターが結果をマージ（重複除去・対応関係整理）→ `TeamDelete` でチーム解散

詳細は `references/workflow-spec.md` の「Phase 1 チーム通信ルール」「マージ仕様」を参照。

## Phase 1.5: タイトル生成＆評価（ユーザー選択ゲート）

Phase 1 のマージ済みリサーチを入力に、5 ステップでタイトルを確定する。詳細手順とプロンプトテンプレは `references/title-workflow.md` 参照。

| Step | エージェント / 主体 | 内容 |
|---|---|---|
| A | `title-generator` | 5パターン × 各 4 個 = **20 個**生成（疑問形／損失回避／数値／変化／秘密） |
| B | `title-evaluator`（プロ SNS マーケター役） | 5 軸（フック／心理／可読／BB思想／リスク）× 各 20 点で採点・ランキング化 |
| C | オーケストレーター | TOP10 を理由込みでユーザーに提示。残り 10 件は折りたたみ |
| D | ユーザー | TOP1 を選択（Phase 2 起動はここがブロッキングゲート） |
| E | Phase 2 各エージェント | 採用タイトルを自メディア用に微調整（カルーセル 13-25 字／Note 30-40 字／X 25-40 字） |

参照: `references/title-playbook.md`（5パターンの心理メカニズム・サムネ工学・2026 トレンド・NG パターン）、`references/title-workflow.md`（採点基準・出力形式）

## Phase 2: 3メディア並列生成

Phase 1.5 確定タイトル原案＋マージ済みリサーチを渡し、以下 3 エージェントを **同一メッセージ内で同時起動**する。

| name | 担当 | 出力 |
|---|---|---|
| `carousel-writer` | `tiktok-fit-carousel-script` | 台本＋キャプション（3500 字以上） |
| `note-writer` | グローバル `note-writer` スキル | 3000-4000 字の知識発信記事 |
| `x-post-writer` | 本スキル＋ `references/x-post-style.md` | long（1500-2500 字、既定）or short（280 字以内） |

各エージェントは Phase 1.5 のタイトルを **自メディア制約に合わせて微調整**し、出力先頭に「採用タイトル（{メディア名}微調整版）」を明記する（`references/title-workflow.md` Step E 参照）。

各エージェントへの ★絶対遵守★ 事項：

- 台本は各スライドをテキスト形式で出力（テーブル形式 NG）。「メイン・大・赤」をヘッダー行に書き、次行からテキスト
- 各スライドに感情誘発 4 型（裏切り／桁スケール／対比／自分事化）のいずれか 1 型以上を組み込む
- カルーセルキャプションは 3,500 字以上必須。Markdown 記号（`**`、`##`、`—`、`／`）を本文に残さない
- Note 記事は note-writer の Phase 1（調査）をスキップし Phase 2（執筆）から開始
- `references/writing-style.md` を全メディア必須遵守（プロトコル禁止、AI っぽさ排除、言い切り）

## Phase 3: 薬機法チェック（3メディア一括）

Phase 2 の 3 つの出力をまとめて `tiktok-fit-compliance-check` に渡す。修正が必要な箇所は各メディアの該当テキストを修正する。

## Phase 4: Notion 保存（同一 DB・3 ページ）

`tiktok-fit-notion-publisher` で同一テーマ・別ページとして保存。`content_type` で区別。

スキーマと title_candidates 学習ログ（4ブロック構成：採用案／TOP10ランキング／パターン別ベスト／マーケター総評）の詳細は `references/notion-publishing.md` 参照。

**★キャプション保存ガード（必須）**: カルーセルページ保存前に、キャプション 3,500 字以上が `sections.caption` に含まれているか必ず確認。欠損時は保存中断 → carousel-writer 出力から取得 → 追加してから保存。

## Phase 5: カルーセル画像生成（ユーザー承認後）

Phase 4 完了後、ユーザーに必ず確認：

```
Notion 保存完了しました。
続けてカルーセル画像（1080×1080 PNG）を生成しますか？
```

承認時のみ `tiktok-fit-slide-renderer` スキルに **委譲**する。本スキルは bash コマンド詳細を持たず、`tiktok-fit-slide-renderer/SKILL.md` の手順に従って実行する。出力先は `$BB_IMAGE_DIR/<slug>/`（未設定時 `./output/投稿画像/<slug>/`）。

未承認時：Phase 5 をスキップし、台本 MD のパスのみ伝える（手動実行用）。

---

## 必須ゲート

各 Phase の品質ゲートは `references/quality-gates.md` に集約。1つでも未達なら次 Phase に進まない。特に重要：

- **Phase 1.5 ユーザー選択ゲート**: ユーザーが TOP1 を明示選択するまで Phase 2 起動禁止
- **キャプション 3500 字ゲート**: カルーセル必須
- **Phase 4 ★キャプション保存ガード**: Notion 保存前確認
- **Phase 5 ユーザー承認ゲート**: 画像生成前確認

## 文章スタイル（★全メディア必須）

X 投稿・Note 記事・カルーセルキャプションのすべてで `references/writing-style.md` を必ず遵守する。特に：

- 「プロトコル」絶対禁止
- Markdown 記号（`**`、`##`、`—`、`：`半角スペース、`／`）を本文に残さない
- 「結論から言うと」「以下では解説します」「ステップ1：」等の説明書語彙を避ける
- 「ケースバイケース」「一概には言えませんが」で逃げない。言い切る
- 定番比喩（地図、羅針盤、土台、車の両輪、潤滑油、DNA、スパイス）を使わない
- 一次情報・主観・偏見を積極的に入れる

---

## 参照ファイル

| ファイル | 内容 |
|---|---|
| `references/category-router.md` | Phase 0 カテゴリ自動判定シグナル・信頼度計算・提示フォーマット |
| `references/workflow-spec.md` | カテゴリ別必須項目・Phase 1 チーム通信・10枚感情設計・出力制約 |
| `references/title-playbook.md` | バズ理論（5パターン心理学・サムネ工学・2026 トレンド・NG） |
| `references/title-workflow.md` | Phase 1.5 詳細手順（プロンプト・採点基準・提示形式） |
| `references/x-post-style.md` | X 投稿生成ルール（long/short モード・Note URL 運用） |
| `references/notion-publishing.md` | Notion 保存スキーマ（title_candidates 学習ログ含む） |
| `references/output-spec.md` | 出力順仕様・メディア別タイトル微調整方針・カテゴリ配分目標 |
| `references/quality-gates.md` | 各 Phase 品質ゲート一覧 |
| `references/writing-style.md` | AI っぽさ排除・禁止ワード・文章チェックリスト |
| `CONTRIBUTING.md` | 改修ルール・肥大化防止規約 |
