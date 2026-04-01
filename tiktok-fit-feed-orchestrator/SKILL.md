---
name: tiktok-fit-feed-orchestrator
description: 日本語の筋トレ情報アカウント向けに、フィード投稿（画像カルーセル）をテーマ別ワークフローで統合実行するスキル。保存数最大化を目的に、調査・投稿単位競合分析・台本化・薬機法と表現チェックを行い、完了後はNotion保存まで一気通貫で実行したい時に使う。
---

# TikTok Fit Feed Orchestrator

## 概要

このスキルは入口専用。テーマを受け取り、カテゴリ判定、深掘り判定、下位スキル実行、最終成果物の整形、Notion保存までを担当する。

**エージェントチーム対応**: Phase 1（リサーチ＋競合分析）をエージェントチームで並列実行し、相互通信による品質向上と処理時間短縮を実現する。

## 固定プロファイル

- KPI: 保存数、およびコメント数（ニーズ収集）
- コンセプト: 筋トレ中・上級者向けに、コンディショニングや努力を最大化するための栄養学・サプリ情報を提供する。情弱ビジネスを終わらせる側。正すのではなく、潰す。
- 深掘り数値基準: 保存率0.5%以上
- 対象: 20-40代男性、筋トレ中級以上
- 文章レベル: 高校生が理解できる日本語
- 口調: 情熱が見える怒り。事実で殴り、思想を叫ぶ。フレンドリーさより"本気さ"を出す。体言止め可。
- 形式: 画像カルーセル投稿（9〜12枚可変）
- 出力形式: Markdown

## BBの思想

- 敵: 「知らない」につけ込んで金を抜く奴ら全員
- 信念: 正しい情報はタダで届けられる。俺らが証明する
- 姿勢: 京大の研究者と薬剤師が、論文と法律で殴る
- 宣言: 「情弱ビジネスを、終わらせる。」

## 起動フロー（インタラクティブモード）

`/tiktok-fit-feed-orchestrator` を引数なしで呼んだ場合、以下の順で対話する。

**Step 1: カテゴリ選択を提示する**

```
カテゴリを選んでください。

1. 比較系（compare）      〇〇 vs 〇〇
2. 成分解説系（ingredient） 牛乳・アシュワガンダ等
3. エンタメ系（entertainment） 固有名詞×空想科学読本
4. 誤認訂正系（debunk）    世間の間違いを正す
```

**Step 2: テーマを質問する**

カテゴリ選択を受け取ったら:
```
テーマを教えてください。
```

**Step 3: フルフロー実行**

テーマを受け取ったら、選択されたカテゴリとテーマでフルフロー（Phase 1 → Phase 2）を実行する。

---

## コマンド

- `/tiktok_discriber カテゴリ テーマ`（カテゴリとテーマを直接指定する場合）

補助コマンド:

- `/deep-dive テーマ`
- `/standard テーマ`

## 実行順（エージェントチーム方式）

### Phase 1: 並列チーム（research + competitor-analysis）

Agent ツールで以下の2エージェントを**同一メッセージ内で同時に起動**する。それぞれ `name` パラメータを指定し、`SendMessage` による相互通信を有効化する。

| チームメンバー | name | 担当スキル | 役割 |
|---|---|---|---|
| リサーチャー | `researcher` | `tiktok-fit-research` | 科学的根拠・PubMed・公式データの収集 |
| 競合アナリスト | `competitor-analyst` | `tiktok-fit-post-competitor-analysis` | TikTok/YouTube/Instagramの競合投稿分析 |

#### 相互通信プロトコル

1. **researcher → competitor-analyst**（早期共有）
   - リサーチの序盤で「主要キーワード」「発見した切り口」を `SendMessage({to: "competitor-analyst"})` で共有する
   - 競合アナリストはこの情報を使い、**既存投稿がカバーしていない独自角度**を優先的に探す

2. **competitor-analyst → researcher**（差別化リクエスト）
   - 競合分析で「多くの投稿が触れていない盲点」を発見したら `SendMessage({to: "researcher"})` でリサーチャーに追加調査を依頼する
   - リサーチャーはその盲点に対するエビデンスを補強する

3. **合流条件**
   - 両エージェントが完了した時点で、オーケストレーター（メインエージェント）が結果をマージする
   - マージ時に重複トピックを除去し、リサーチ結果と競合分析結果の対応関係を整理する

#### Phase 1 の起動テンプレート

```
Agent 1（並列起動）:
  name: "researcher"
  subagent_type: "general-purpose"
  prompt: |
    テーマ「{theme}」について tiktok-fit-research スキルに従い調査を実行せよ。
    カテゴリ: {workflow}、深掘りモード: {depth_mode}。
    調査序盤で主要キーワードと発見した切り口を SendMessage({to: "competitor-analyst"}) で共有せよ。
    competitor-analyst から追加調査依頼が来たら対応せよ。

Agent 2（並列起動）:
  name: "competitor-analyst"
  subagent_type: "general-purpose"
  prompt: |
    テーマ「{theme}」について tiktok-fit-post-competitor-analysis スキルに従い競合分析を実行せよ。
    カテゴリ: {workflow}。
    researcher からキーワード共有が届いたら、そのキーワードで既存投稿がカバーしていない独自角度を重点的に探せ。
    盲点を発見したら SendMessage({to: "researcher"}) で追加調査を依頼せよ。
```

### Phase 2: 直列実行（script → compliance → notion）

Phase 1 の結果をマージした後、以下を順番に実行する。

3. `tiktok-fit-carousel-script`（Phase 1 のマージ結果を入力として台本生成）
4. `tiktok-fit-compliance-check`（台本を入力として薬機法チェック）
5. `tiktok-fit-notion-publisher`（全成果物をNotion保存）

### フォールバック

エージェントチーム機能が利用できない環境では、従来の直列実行にフォールバックする:

1. `tiktok-fit-research`
2. `tiktok-fit-post-competitor-analysis`
3. `tiktok-fit-carousel-script`
4. `tiktok-fit-compliance-check`
5. `tiktok-fit-notion-publisher`

## Notion保存ルール

- 最終成果物は毎回 `tiktok-fit-notion-publisher` に渡して即時保存する
- `sections.title_suggestions`、`sections.research`、`sections.compliance_check`、`sections.script`、`sections.summary_table`、`sections.references` を必ず埋める
- workflow はこのスキルで最終決定したカテゴリをそのまま引き継ぐ
- 保存に必要な項目が欠けている場合のみ、欠損項目を補ってから保存する

## 深掘り条件

以下のどれかで深掘りにする。

- 保存率が0.5%以上
- 作用機序を誤解すると実践を間違えやすい
- 筋トレ界隈のトレンド性が高い

## 出力仕様

必ずこの順で返す。**タイトル改善案は最初の独立セクションとして必ず出力すること。台本やキャプションの中に埋め込まず、明確に分離する。**

1. `タイトル改善案（5つ）`（★必須・最初に出力）ユーザーが入力したテーマに対して、よりフックが強くクリックされやすいタイトル案を5つ提示する。番号付きリストで出力し、Notion保存時は `sections.title_suggestions` に格納する。
2. `台本`（スタイルメタデータ付きフォーマット。各スライドにテキスト・サイズ・色・感情ラベルを付与）
3. `キャプション`（3500字以上の長文キャプション）
4. `素材管理表`
5. `総まとめ表（1枚分の設計）`（Markdown表形式。1行あたり3〜4列。列名はテーマに合わせて柔軟に）
6. `根拠リンク`
7. `薬機法・表現チェック結果`
8. `Notion保存結果`

## カテゴリ配分の運用目標

- compare（比較系）: 30%
- debunk（誤認訂正系）: 30%
- ingredient（成分解説系）: 25%
- entertainment（エンタメ系）: 15%

## 必須ゲート

- 日本語ソース優先ゲート
- 保存率0.5%閾値ゲート
- 分かりやすさゲート（高校生レベル）
- 総まとめ表ゲート（1投稿につき1枚必須）
- 感情設計ゲート（各スライドに感情ラベルが付与されているか）
- スタイルメタデータゲート（各スライドにテキスト・サイズ・色が付与されているか）
- コメント誘導ゲート（CTAが承認欲求を刺激する問い形式になっているか）
- 薬機法・表現ゲート
- Notion保存完了ゲート

## 参照

- `references/workflow-spec.md`
- `references/performance-baseline.md`
- `scripts/workflow_router.py`
