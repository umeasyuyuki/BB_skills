---
name: contents-fullmake
description: 日本語の筋トレ情報アカウント向けに、テーマを1つ入力するだけでTikTokカルーセル台本+画像、Note記事、X投稿の3メディアを一気通貫で生成するスキル。リサーチ・競合分析・執筆・薬機法チェック・Notion保存・カルーセル画像生成まで全自動で実行する。
---

# Contents Fullmake（旧 TikTok Fit Feed Orchestrator）

## 概要

このスキルは入口専用。テーマを受け取り、カテゴリ判定、深掘り判定、下位スキル実行、最終成果物の整形、Notion保存、カルーセル画像生成までを担当する。

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

`/contents-fullmake` を引数なしで呼んだ場合、以下の順で対話する。

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

- `/contents-fullmake`（引数なし。対話モードで起動）
- `/contents-fullmake カテゴリ テーマ`（カテゴリとテーマを直接指定する場合）

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

#### 相互通信のやり取り

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

### Phase 2: 3メディア並列生成

Phase 1 の結果をマージした後、**3つのコンテンツを同時に生成**する。

Agent ツールで以下の3エージェントを**同一メッセージ内で同時に起動**する。

| メディア | name | 担当 | 出力 |
|---|---|---|---|
| カルーセル | `carousel-writer` | `tiktok-fit-carousel-script` | 台本＋キャプション（3500字以上） |
| Note記事 | `note-writer` | `note-writer` スキル | 3000-4000字の知識発信記事 |
| X投稿 | `x-post-writer` | 本スキル内のX投稿生成ルール | 280字以内のフック投稿 |

#### 各メディアの役割

| メディア | 役割 | 深さ | KPI |
|---|---|---|---|
| カルーセル | 保存・コメント誘導 | フック＋結論（浅く広く） | 保存数・コメント数 |
| Note記事 | SEO＋信頼構築 | メカニズム深掘り | PV・滞在時間 |
| X投稿 | 拡散・流入導線 | 最強の1行 | RT・いいね |

#### Phase 2 の起動テンプレート

```
Agent 1（並列起動）:
  name: "carousel-writer"
  subagent_type: "general-purpose"
  prompt: |
    テーマ「{theme}」について tiktok-fit-carousel-script スキルに従い台本を生成せよ。
    カテゴリ: {workflow}。
    以下のマージ済みリサーチ結果を入力として使え:
    {merged_research}

Agent 2（並列起動）:
  name: "note-writer"
  subagent_type: "general-purpose"
  prompt: |
    テーマ「{theme}」について note-writer スキルに従い Note 記事を生成せよ。
    ワークフロー: Phase 1 のリサーチ結果を入力として使い、Phase 1（調査）をスキップして Phase 2（執筆）から開始せよ。
    リサーチパッケージ:
    {merged_research}

Agent 3（並列起動）:
  name: "x-post-writer"
  subagent_type: "general-purpose"
  prompt: |
    テーマ「{theme}」について X 投稿（280字以内）を生成せよ。
    X投稿生成ルール（後述）に従うこと。
    リサーチ結果:
    {merged_research}
```

### Phase 3: 薬機法チェック（3メディア一括）

Phase 2 の3つの出力をまとめて `tiktok-fit-compliance-check` に渡す。

- カルーセル台本＋キャプション
- Note記事本文
- X投稿本文

3メディア分を一括でチェックし、修正が必要な箇所があれば各メディアの該当テキストを修正する。

### Phase 4: Notion保存（同一DB・3ページ）

3つのコンテンツを `tiktok-fit-notion-publisher` で**同一テーマ・別ページ**として保存する。

| ページ | content_type | 含むセクション |
|---|---|---|
| カルーセル | `carousel` | title_suggestions, research, script, caption, compliance_check, summary_table, references |
| Note記事 | `note` | title_suggestions, body, references |
| X投稿 | `x_post` | body, references |

`content_type` プロパティでフィルタリングできるため、同一DBで管理可能。

### Phase 5: カルーセル画像生成（ユーザー承認後）

Phase 4 完了後、ユーザーに画像生成の実行可否を必ず確認する：

```
Notion保存完了しました。
続けてカルーセル画像（1080×1080 PNG）を生成しますか？
```

ユーザーが承認した場合の実行手順:

1. **台本MD をローカル保存**
   - `tiktok-fit-slide-renderer/data/pipeline/drafts/<slug>.md` に保存する
   - slug は Notion保存時のスライド名と合わせる

2. **Phase 1 パース実行**
   ```bash
   cd tiktok-fit-slide-renderer
   python3 scripts/render_slides.py --parse --input data/pipeline/drafts/<slug>.md
   ```
   - 出力された YAML マニフェストのパスと、スライド一覧・バリデーション警告を表示する

3. **ユーザー編集の機会を提供**
   ```
   YAMLマニフェストを確認しました。
   テキストや色を修正しますか？それともこのまま生成を開始しますか？
   ```
   - 修正指示が来た場合は Edit ツールで YAML を直接編集する
   - 変更内容を `feedback_log.jsonl` に記録する（`--log --entry '{...}'`）

4. **Phase 3 レンダリング実行**
   ```bash
   python3 scripts/render_slides.py --render --manifest data/pipeline/drafts/<slug>_render_manifest.yaml
   ```
   - 11枚のPNGが `data/pipeline/images/<slug>/` に生成される
   - 成功/失敗の枚数を報告

5. **出力先を開く提案**
   ```
   画像生成完了。11枚のPNGが生成されました。
   Finder/Explorer で確認しますか？ → `open data/pipeline/images/<slug>/`
   ```

**ユーザーが承認しなかった場合**: Phase 5 をスキップして、台本MDのパスだけ伝える（後で手動実行できるように）。

### フォールバック

エージェントチーム機能が利用できない環境では、直列実行にフォールバックする:

1. `tiktok-fit-research`
2. `tiktok-fit-post-competitor-analysis`
3. `tiktok-fit-carousel-script`（カルーセル台本＋キャプション）
4. `note-writer`（Note記事。Phase 1 のリサーチ結果を入力とし、note-writer の Phase 1 をスキップ）
5. X投稿生成（本スキル内ルールに従い直接生成）
6. `tiktok-fit-compliance-check`（3メディア一括）
7. `tiktok-fit-notion-publisher`（3ページ保存）
8. `tiktok-fit-slide-renderer`（カルーセル画像生成、ユーザー承認後のみ）

## X投稿生成ルール

Phase 2 の `x-post-writer` が従うルール。

### モード分岐

X投稿は **long モード（1500〜2500字）** を**既定**とする。Note誘導を最強にするため。
瞬発的なコメント誘発のみ狙う場合は **short モード（280字以内）** を使う。

### 共通の前提

- `references/writing-style.md` の全ルールを遵守（プロトコル禁止、AIっぽさ排除、言い切り）
- 日本語
- BBの口調（情熱が見える怒り、体言止め可、体験談・主観・偏見を積極的に入れる）
- 一次情報と数字（論文の数・摂取量・期間等）で殴る

---

### long モード（1500〜2500字／Note誘導強化）

Note記事と連動する投稿はこちらを使う。**これが既定モード**。

#### 構成

以下の9ブロックで書く：

1. **フック＋変化の予告**（200〜300字）
   - 常識を覆す1行から始める
   - 書いた人自身の変化を数字で示す（例：月5000円減った、ベンチ10kg伸びた）
   - 「これを知らないとヤバい」という危機感を匂わせる

2. **自己紹介＋権威性**（150〜250字）
   - 「京大の研究者と薬剤師のチーム」「論文147本読んだ」等の根拠
   - 読者との距離を縮める個人的な書き方

3. **問題提起**（200〜300字）
   - 情弱インフルエンサーが言っていることを具体的に列挙
   - それを「全部根拠が薄い」等で否定する

4. **本論（3〜5パート）**（700〜1100字）
   - 結論の数字・数式
   - 作用機序や根拠となる研究
   - 失敗例・成功例の対比

5. **具体例・ストーリー**（150〜250字）
   - リアルな体験談、実測データ、失敗ログ
   - 読者が自分ごと化できる場面

6. **Note誘導の橋渡し**（80〜150字）
   - 「本記事はnote記事の一部」「他にもあります」等の自然な接続
   - 押し付けがましい書き方はしない

7. **Note限定の具体的追加価値**（200〜300字・★最重要）
   - 配布物（MDファイル、計算表、チェックリスト）
   - 深いデータ（体重別表、商品比較、食品DB）
   - 関連記事群
   - 3つ以上を箇条書きで明示する

8. **忙しい人向け代替案**（80〜150字）
   - 「記事読む時間ない人は、配布ファイルだけでOK」等
   - 読まない層にも選択肢を与える

9. **締め＋URL＋ハッシュタグ**（80〜150字）
   - BBの決め台詞（例：情弱ビジネスを、終わらせる）
   - note URL
   - ハッシュタグ2〜3個

#### 書き方の原則

- 見出しは本文の流れを止めない程度に（`## 見出し` ではなく自然な段落分けでもOK）
- 数字・固有名詞・論文名を散りばめる
- 段落は2〜4行で区切る（スクロール読みに耐える）
- 語尾を揃えすぎない（「〜です」「〜ました」「体言止め」を混ぜる）

---

### short モード（280字以内／コメント誘発・瞬発力）

単発ネタ・カルーセル投稿に連動する瞬発型のみ使う。

#### 構成

```
{フック（最強の1行）}

{補足1行（数値 or 対比構造）}

{CTA or 導線}

#ハッシュタグ1 #ハッシュタグ2
```

#### フックの設計原則

- カルーセルの1枚目（挑発）のテキストを凝縮する
- 「え？」と思わせる数値 or 対比構造を先頭に置く
- 句読点を最小限にし、改行で区切る

#### 導線の設計

- Noteへの誘導：「Note版に配布物と一覧表あり→URL」
- カルーセルへの誘導：「カルーセルで全部見せた→プロフから」
- リンクなし：数式CTA（`A(単位) × B(単位) = ?`）で締める

---

### 出力形式

```markdown
# X投稿（mode: long / short）

{投稿本文}

---
文字数: {N}字
モード: long / short
ハッシュタグ: #xxx #yyy
導線: Note / カルーセル / なし
```

## Notion保存ルール

- 最終成果物は毎回 `tiktok-fit-notion-publisher` に渡して即時保存する
- **3メディア分を同一DB・別ページとして保存する（content_type で区別）**
- workflow はこのスキルで最終決定したカテゴリをそのまま引き継ぐ
- 保存に必要な項目が欠けている場合のみ、欠損項目を補ってから保存する

### カルーセル（content_type: carousel）

`sections.title_suggestions`、`sections.research`、`sections.compliance_check`、`sections.script`、`sections.caption`（★必須）、`sections.summary_table`、`sections.references` を必ず埋める。台本のスタイルメタデータ（メイン・大・赤 等）はNotion装飾に変換して保存する。

### Note記事（content_type: note）

`sections.title_suggestions`、`sections.body`（記事本文）、`sections.references` を埋める。

### X投稿（content_type: x_post）

`sections.body`（投稿本文）、`sections.references` を埋める。

## 深掘り条件

以下のどれかで深掘りにする。

- 保存率が0.5%以上
- 作用機序を誤解すると実践を間違えやすい
- 筋トレ界隈のトレンド性が高い

## 出力仕様

必ずこの順で返す。**タイトル改善案は最初の独立セクションとして必ず出力すること。台本やキャプションの中に埋め込まず、明確に分離する。**

### カルーセル（メイン出力）

1. `タイトル改善案（5つ）`（★必須・最初に出力）ユーザーが入力したテーマに対して、よりフックが強くクリックされやすいタイトル案を5つ提示する。番号付きリストで出力し、Notion保存時は `sections.title_suggestions` に格納する。
2. `台本`（スタイルメタデータ付きフォーマット。各スライドにテキスト・サイズ・色・感情ラベルを付与）
3. `キャプション`（★必須・3500字以上の長文キャプション。Notion保存時は `sections.caption` に格納する）
4. `素材管理表`
5. `総まとめ表（1枚分の設計）`（Markdown表形式。1行あたり3〜4列。列名はテーマに合わせて柔軟に）
6. `根拠リンク`

### Note記事

7. `Note記事`（3000-4000字。note-writer スキルの黄金構成テンプレートに従う）

### X投稿

8. `X投稿`（280字以内。X投稿生成ルールに従う）

### 共通

9. `薬機法・表現チェック結果`（3メディア一括）
10. `Notion保存結果`（3ページ分のURLを出力）
11. `カルーセル画像生成結果`（Phase 5を実行した場合のみ。出力ディレクトリと生成枚数）

## カテゴリ配分の運用目標

- compare（比較系）: 30%
- debunk（誤認訂正系）: 30%
- ingredient（成分解説系）: 25%
- entertainment（エンタメ系）: 15%

## 必須ゲート

### カルーセル
- 日本語ソース優先ゲート
- 保存率0.5%閾値ゲート
- 分かりやすさゲート（高校生レベル）
- 総まとめ表ゲート（1投稿につき1枚必須）
- 感情設計ゲート（各スライドに感情ラベルが付与されているか）
- スタイルメタデータゲート（各スライドにテキスト・サイズ・色が付与されているか）
- コメント誘導ゲート（CTAが `A × B = ?` 数式テンプレート形式になっているか）
- キャプション文字数ゲート（3500字以上）

### Note記事
- 文字数ゲート（3000-4000字）
- 黄金構成テンプレート準拠ゲート

### X投稿
- 文字数ゲート（280字以内）
- フック設計ゲート（先頭1行で「え？」を引き出せるか）

### 共通
- 薬機法・表現ゲート（3メディア一括）
- Notion保存完了ゲート（3ページ全て保存されているか）

### Phase 5 実行時のみ
- ユーザー承認ゲート（画像生成前に必ず確認を取ったか）
- バリデーション通過ゲート（--render 前に --validate でエラーなし確認）
- 画像生成完了ゲート（全スライドがPNG化されているか）

## 文章スタイル（★全メディア必須）

**X投稿・Note記事・カルーセルキャプションのすべてで、`references/writing-style.md` を必ず遵守する。**

特に以下を厳守：
- 「プロトコル」という言葉は絶対に使わない
- Markdown記号（`**太字**`、`##`、`—`、`：` 半角スペース、`／`）を本文に残さない
- 「結論から言うと」「以下では解説します」「ステップ1：」等の説明書っぽい書き方を避ける
- 「ケースバイケース」「一概には言えませんが」で逃げない。言い切る
- 定番比喩（地図、羅針盤、土台、車の両輪、潤滑油、DNA、スパイス）を使わない
- 一次情報・主観・偏見を積極的に入れる

詳細と実務チェックリストは `references/writing-style.md` を参照。

## 参照

- `references/writing-style.md`（★全メディア必須）
- `references/workflow-spec.md`
- `references/performance-baseline.md`
- `scripts/workflow_router.py`
