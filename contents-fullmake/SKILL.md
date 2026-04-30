---
name: contents-fullmake
description: テーマ1つで TikTok カルーセル台本＋画像を一気通貫生成。BB（筋トレ情報）アカウント専用。リサーチ・競合分析・タイトル評価・薬機法チェック・Notion 保存まで自動。Note 記事と Threads 投稿は bb-note-threads スキルに分離（テキスト媒体専用の独立動線）。
---

<!--
このファイルはコア手順のみ。詳細仕様は references/ 配下に分離。
上限: 250 行 / 10KB（CONTRIBUTING.md 参照）。
1改修ごとに +30 行を超える追加は references/ への切り出しを検討すること。
肥大化チェック: ../scripts/check_skill_size.sh を改修後に必ず実行。
-->

# Contents Fullmake

## 概要

入口専用スキル。テーマを受け取り、カテゴリ判定 → 調査 → タイトル評価 → カルーセル台本生成 → 薬機法チェック → Notion 保存 → カルーセル画像生成までを担当する。Phase 1 はエージェントチームで並列実行する。

Note 記事 / Threads 投稿の生成は **本スキルから分離**された `bb-note-threads` スキルが担当する（テキスト媒体専用の独立動線）。本スキルは TikTok カルーセル投稿のみを扱う。

## 固定プロファイル

- KPI: 保存数、コメント数（ニーズ収集）
- コンセプト: 筋トレ中・上級者向け。コンディショニングや努力を最大化するための栄養学・サプリ情報を、わかりやすく届ける
- 深掘り基準: 保存率 0.5% 以上
- 対象: 20-40 代男性、筋トレ中級以上
- 文章レベル: 高校生が理解できる日本語
- 口調: **お兄ちゃん的なノリ + 空想科学読本ノリ**。語り口調で、頭にスッと入る。体言止め禁止。比喩・桁スケール・仮想思考を散りばめる
- 形式: 画像カルーセル投稿（**枚数自由、1 画像 1 メッセージ徹底**。目安 8-15 枚、情報量で決まる）
- 出力: Markdown

## BB のチームと姿勢

- **チーム**: Brain Bulking — 京大院生と薬剤師が集まったチーム
- **役割**: フィットネス・ヘルスケアの科学を、お兄ちゃんが教えてくれる感覚で届ける
- **姿勢**: 論文・現場・ちょっとの想像力で、フィットネスを面白くする
- **届け方**: 怒りで殴るんじゃなくて、知ったらちょっと得した気分になる科学を、楽しく
- **一人称**: 「俺ら」「俺たち」（維持）

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

## Phase 1: リサーチ（researcher 単独）

`tiktok-fit-research` を `researcher` エージェントとして起動し、科学的根拠・PubMed・公式データを収集する。差別化軸（独自角度の抽出）は researcher の調査範囲に含める。

| name | 担当スキル | 役割 |
|---|---|---|
| `researcher` | `tiktok-fit-research` | 科学的根拠・PubMed・公式データ + 既存情報との差別化軸抽出 |

詳細は `references/workflow-spec.md` の「Phase 1」参照。

## Phase 1.5: タイトル生成＆評価（タイトル自動採用フラグ対応）

Phase 1 のリサーチを入力に、5 ステップでタイトルを確定する。詳細手順とプロンプトテンプレは `references/title-workflow.md` 参照。

| Step | エージェント / 主体 | 内容 |
|---|---|---|
| A | `title-generator` | 5パターン × 各 2 個 = **10 個**生成（疑問形／損失回避／数値／変化／秘密） |
| B | `title-evaluator`（プロ SNS マーケター役） | 5 軸（フック／心理／可読／BB思想／リスク）× 各 20 点で採点・ランキング化 |
| C | オーケストレーター | TOP5 を理由込みで提示 |
| D | ユーザー or AI 自動 | **`--auto-title` フラグ未指定** → ユーザー選択（ブロッキングゲート）/ **指定時** → AI 採点 TOP1 を自動採用 |
| E | Phase 2 carousel-writer | 採用タイトルをカルーセル 1 枚目用に微調整（13-25 字） |

### `--auto-title` フラグ

```
/contents-fullmake テーマ --auto-title
```

AI 採点 TOP1 を自動採用し、ユーザー選択待ちをスキップ。Notion 保存後、必要なら手動でタイトル差し替え可能。**スピード優先運用**で使う（10 分以内目標達成のため）。

参照: `references/title-playbook.md`（5パターンの心理メカニズム・サムネ工学・2026 トレンド・NG パターン）、`references/title-workflow.md`（採点基準・出力形式）

## Phase 2: カルーセル台本生成

Phase 1.5 確定タイトル原案＋マージ済みリサーチを渡し、`carousel-writer` を起動する。

| name | 担当 | 出力 |
|---|---|---|
| `carousel-writer` | `tiktok-fit-carousel-script` | 台本＋キャプション（3500 字以上） |

`carousel-writer` は Phase 1.5 のタイトルを **カルーセル 1 枚目用に微調整**（13-25 字）し、出力先頭に「採用タイトル（カルーセル微調整版）」を明記する（`references/title-workflow.md` Step E 参照）。

★絶対遵守★ 事項：

- 台本は各スライドをテキスト形式で出力（テーブル形式 NG）。「メイン・大・赤」をヘッダー行に書き、次行からテキスト
- 各スライドに感情誘発 4 型（裏切り／桁スケール／対比／自分事化）のいずれか 1 型以上を組み込む
- カルーセルキャプションは 3,500 字以上必須。Markdown 記号（`**`、`##`、`—`、`／`）を本文に残さない
- `references/writing-style.md` を必須遵守（プロトコル禁止、AI っぽさ排除、言い切り）
- **TikTok カルーセルには LINE オープンチャット URL を絶対に入れない**（`references/line-oc.md` 参照、Threads / Note 専用動線）

Note 記事 / Threads 投稿が必要な場合は、別途 `bb-note-threads` スキルを起動する（こちらはタイトル投入で動作）。

## Phase 3: 薬機法チェック

Phase 2 のカルーセル台本＋キャプションを `tiktok-fit-compliance-check` に渡す。修正が必要な箇所は該当テキストを修正する。

## Phase 4: Notion 保存（同一 DB・1 ページ）

`tiktok-fit-notion-publisher` で `content_type: carousel` ページとして保存。

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

## 文章スタイル（★必須）

カルーセルキャプション・台本本文のすべてで `references/writing-style.md` を必ず遵守する。新キャラ（お兄ちゃんノリ + 空想科学読本ノリ）の核心ルール：

- **体言止めは禁止**（「〜の正体」「〜が鍵」NG → 「〜なんだよね」「〜だよ」で語る）
- 語り口調で、頭にスッと入る文体に（「実はさ」「ちょっと意外なんだけど」「面白いのが」を活用）
- **空想科学読本ノリ**を散りばめる（比喩・桁スケール感・「もし〇〇だったら」の仮想思考）
- 「プロトコル」「最適化」「アプローチ」絶対禁止
- Markdown 記号（`**`、`##`、`—`、`：`半角スペース、`／`）を本文に残さない
- 「結論から言うと」「以下では解説します」「ステップ1：」等の説明書語彙を避ける
- 「ケースバイケース」「一概には言えませんが」で逃げない。やわらかく言い切る
- 定番比喩（地図、羅針盤、土台、車の両輪、潤滑油、DNA、スパイス）を使わない。**読者が見たことのある具体的な物**で例える
- 一次情報・主観・体験を積極的に入れる
- 「俺らはこの構造が許せない」のような怒りトーンは封印（科学を楽しく届けるスタンスに統一）

---

## 参照ファイル

| ファイル | 内容 |
|---|---|
| `references/category-router.md` | Phase 0 カテゴリ自動判定シグナル・信頼度計算・提示フォーマット |
| `references/workflow-spec.md` | カテゴリ別必須項目・Phase 1 仕様・感情設計フレームワーク・出力制約 |
| `references/title-playbook.md` | バズ理論（5パターン心理学・サムネ工学・2026 トレンド・NG） |
| `references/title-workflow.md` | Phase 1.5 詳細手順（プロンプト・採点基準・提示形式） |
| `references/notion-publishing.md` | Notion 保存スキーマ（title_candidates 学習ログ含む） |
| `references/line-oc.md` | LINE OC URL 取り扱いルール（カルーセル絶対禁止） |
| `references/output-spec.md` | 出力順仕様・メディア別タイトル微調整方針・カテゴリ配分目標 |
| `references/quality-gates.md` | 各 Phase 品質ゲート一覧 |
| `references/writing-style.md` | AI っぽさ排除・禁止ワード・文章チェックリスト |
| `CONTRIBUTING.md` | 改修ルール・肥大化防止規約 |
