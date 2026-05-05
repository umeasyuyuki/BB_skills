---
name: bb-note-threads
description: BB（Brain Bulking）専用のテキスト媒体オーケストレーター。タイトル投入1つで、Threads投稿（要点・抽象）とNote記事（深掘り）を並列生成し、ThreadsからNoteへ自然に案内し、Note末尾でプロフィールリンク / 公式リンク集へ温かくつなぐ。TikTokカルーセルとは独立した「Threads → Note → 公式リンク集」動線を作るためのスキル。
---

<!--
このファイルはコア手順のみ。詳細仕様は references/ 配下に分離。
上限: 250 行 / 12 KB（CONTRIBUTING.md 参照）。
1改修ごとに +30 行を超える追加は references/ への切り出しを検討すること。
肥大化チェック: ../scripts/check_skill_size.sh bb-note-threads を改修後に必ず実行。
-->

# BB Note × Threads オーケストレーター

## 概要

タイトル文字列1つを入口に、Threads投稿とNote記事を並列生成し、ThreadsではNoteへの自然な案内だけを置き、Note末尾でプロフィールリンク / 公式リンク集へ温かくつなぐ。TikTokカルーセル生成（contents-fullmake）とは完全に独立した、テキスト媒体専用の動線を構築するためのスキル。

動線設計:

```
Threads（要点・抽象、500-700字）
   ↓ Note URL リンク
Note（深掘り、2500-3500字）
   ↓ プロフィールリンク / 公式リンク集
公式HP・TikTok・他Note・LINEオープンチャット（選択肢の1つ）
```

## 固定プロファイル

- KPI: Threads エンゲージメント率、Note への遷移率、プロフィールリンククリック率、LINE OC 加入数
- コンセプト: 筋トレ中・上級者向け。コンディショニングや努力を最大化するための栄養学・ヘルスケア情報。情弱ビジネスを終わらせる側
- 対象: 20-40 代男性、筋トレ中級以上
- 文章レベル: 高校生が理解できる日本語
- 口調: **標準語**で統一。断定・体言止め可。情熱は事実で語る。AI っぽい曖昧表現・抽象語は禁止（旧仕様の関西弁レベル 2 は廃止）
- 出力: Markdown × 2（Threads / Note）
- 媒体差別化: Threads は要点・抽象・短文、Note は深掘り・SEO・長文
- トーンの使い分け: Threads / Note 本文 = 標準語 BB トーン（断定・体言止め・思想を叫ぶ）/ Threads 最終リプ = 温かく、ゆるい Note 案内 / Note 末尾 = 関連リンク案内（押し付けない・医療相談に見せない）

## BB の思想

- 敵: 「知らない」につけ込んで金を抜く奴ら全員
- 信念: 正しい情報はタダで届けられる。俺らが証明する
- 姿勢: 京大院生と薬剤師が、論文と法律で殴る
- 宣言: 「情弱ビジネスを、終わらせる。」
- コミュニティ位置づけ: LINE オープンチャットはプロフィールリンク / 公式リンク集内の選択肢の 1 つ。Threads では直接案内しない

## 起動フロー

引数の数で分岐する。

| 呼び出し方 | 動作 |
|---|---|
| `/bb-note-threads` | 対話モード：タイトル質問 → フルフロー |
| `/bb-note-threads "タイトル"` | タイトル即採用 → フルフロー |
| `/bb-note-threads "タイトル" --no-competitor` | 競合分析を省略する軽量モード |

カテゴリは 5 種：compare / ingredient / entertainment / debunk / discovery（contents-fullmake と共通、Note案内リプやNote本文の切り口調整に使う）

## Phase 0: タイトル受領

投入されたタイトル文字列をそのまま採用する。タイトル評価フローは持たない（contents-fullmake の Phase 1.5 とは異なる）。

サブステップ:

1. タイトル文字数チェック（13〜30字推奨、超過時は警告のみ）
2. テーマカテゴリ自動判定（5 種）→ Threads / Note の切り口調整に使用
3. 確定タイトルとカテゴリを Phase 1 / Phase 2 に渡す

詳細: `references/workflow-spec.md` の「Phase 0」参照

---

## Phase 1: 並列調査（research + competitor-analysis）

`TeamCreate({team_name: "bb-note-threads-team"})` でチームを作成し、以下 2 エージェントを `team_name` 指定で同時起動する。`SendMessage` による双方向通信を有効化する。

| name | 担当スキル | 役割 |
|---|---|---|
| `researcher` | `tiktok-fit-research` | 科学的根拠・PubMed・公式データの収集 |
| `competitor-analyst` | `tiktok-fit-post-competitor-analysis` | Threads / Note / YouTube の競合投稿分析 |

通信ルール:

1. **researcher → competitor-analyst**（早期共有）: 主要キーワードと発見した切り口を `SendMessage({to: "competitor-analyst"})` で共有
2. **competitor-analyst → researcher**（差別化リクエスト）: 盲点発見時に追加調査依頼
3. **合流**: 両エージェント完了後、オーケストレーターが結果をマージ → `TeamDelete` でチーム解散

`--no-competitor` フラグ指定時は competitor-analyst を起動せず、researcher 単体実行とする。

詳細: `references/workflow-spec.md` の「Phase 1」参照

---

## Phase 2: 並列生成（threads-writer + note-writer）

Phase 1 のマージ済みリサーチを入力に、Threads 投稿と Note 記事を並列生成する。

| name | 役割 | 文体ガイド | 出力構造 |
|---|---|---|---|
| `threads-writer` | Threads 投稿（ツリー構成、4 型から選択） | `references/threads-style.md` | 親 + リプ複数（各 200-300 字） |
| `note-writer` | Note 記事（深掘り・SEO・手紙トーン） | `references/note-style.md` | 2500-3500 字 |

### Threads ツリー構成

Threads は **親ポスト + リプライ複数** のツリー構造で出力する。型ごとにツリー深さが決まっている。

| 型 | 親 | 本体リプ | Note案内リプ | 合計 |
|---|---:|---:|---:|---:|
| ⚪選系 / ランキング系 | 1 | 1 | 1 | 3 |
| 体験談型 / 対比型 | 1 | 2 | 1 | 4 |

本体ポスト（親 + 本体リプ）は 200-300 字、**Note案内リプは 100-180 字**。最終リプに Note URL プレースホルダだけを置き、LINE / プロフィールリンク / 公式リンク集への誘導は Threads には書かない。

### 両エージェント共通の必須要素（Threads 最終リプ / Note 末尾）

- **Threads 最終リプ**: `references/line-oc-templates.md` の「Threads 最終リプ」を参照し、温かくゆるい Note 案内だけを書く
- **Note 末尾**: `references/line-oc-templates.md` の「Note 末尾構造」を参照し、`## 関連リンク` 見出しでプロフィールリンク / 公式リンク集へ案内する
- **健康系免責**: Note 末尾に「個別の医療相談や診断をする場所ではありません。」を入れる

Threads 最終リプには Note URL プレースホルダ（`【★Note URL を貼る★】`）を置く。Note 公開後、Threads 投稿時に手動で URL 差し替え。

詳細: `references/output-spec.md` の「Threads 末尾構造」「Note 末尾構造」参照

---

## Phase 3: 薬機法チェック（並列）

両媒体の本文を `tiktok-fit-compliance-check` に渡し、Red / Yellow / Green 判定を取得する。

- Red 判定: 該当箇所を提示し、Phase 2 にフィードバック → writer エージェントが修正版を出す（最大 2 回まで）
- Yellow 判定: 警告のみ、ユーザーに最終判断を委ねる
- Green 判定: そのまま Phase 4 へ

詳細: `references/quality-gates.md` の「薬機法ゲート」参照

---

## Phase 4: Notion 保存

`tiktok-fit-notion-publisher` を呼び出し、Threads / Note の 2 ページを保存する。

保存後、両ページに `paired_post_url` プロパティで相互リンクを書き込む（Threads → Note の URL、Note → Threads の URL）。

| プロパティ | Threads | Note |
|---|---|---|
| `content_type` | `threads` | `note` |
| `pricing_mode` | `free` | `free`（将来的に `paid` 切替予定） |
| `funnel_stage` | `awareness` | `engagement` |
| `paired_post_url` | Note ページ URL | Threads ページ URL |

詳細: `references/notion-publishing.md` 参照

---

## セルフチェック（出力前必須）

writer エージェントは出力前に `references/quality-gates.md` の 12 項目チェックリストを実行する。特に重要なのは:

- Threads 全体に `line.me`、`LINEオープンチャット`、`完全無料`、`日本最先端`、`ステータス`、`👇` が混入していないか
- Threads 最終リプが Note 案内だけになっているか
- Note 末尾見出しが `## 関連リンク` になっているか
- Note 末尾にプロフィールリンク / 公式リンク集プレースホルダがあるか
- Note 末尾に医療相談・個別診断ではない旨があるか
- AI っぽい曖昧表現（「ケースバイケース」「一概には」等）・抽象語（「最適化」「アプローチ」）が混入していないか
- 関西弁の語尾（「〜やで」「〜ねん」「ほな」「せやから」「めっちゃ」「ほんま」等）が**全文を通じて**混入していないか

---

## TikTok との分離原則

- **TikTok カルーセル**には LINE OC URL を**絶対に入れない**（contents-fullmake/references/line-oc.md と整合）
- **本スキルの Threads**にも LINE OC URL を入れない。Threads は Note URL のみ
- **本スキルの Note**はプロフィールリンク / 公式リンク集へ案内し、その先で LINE OC を選択肢として見せる
- TikTok 用台本生成が必要な場合は `contents-fullmake` を使う（こちらは TikTok カルーセル専用に縮退済み）

---

## エラー時の挙動

- Phase 1 で researcher / competitor-analyst が両方失敗した場合: 中断、ユーザーにエラー報告
- Phase 2 で writer が失敗した場合: もう一方の writer 結果は保持、失敗側のみリトライ
- Phase 3 で Red 判定が 2 回続いた場合: ユーザーに手動修正を依頼
- Phase 4 で Notion 保存失敗時: ローカルファイルに `output/<timestamp>/` でバックアップ保存

---

## 参考ファイル

- `references/workflow-spec.md` — Phase 詳細・エージェント通信仕様
- `references/tone-guide.md` — **文体・トーンガイド（標準語ベース、共通、必読）**
- `references/threads-style.md` — Threads 文体ガイド（ツリー構成・4 型）
- `references/note-style.md` — Note 文体ガイド（標準語 BB トーン）
- `references/line-oc-templates.md` — 関連リンク・コミュニティ案内テンプレ（Threads の Note 案内 + Note 末尾の温かいリンク案内）
- `references/output-spec.md` — 出力フォーマット定義
- `references/notion-publishing.md` — Notion 保存仕様
- `references/quality-gates.md` — セルフチェック・薬機法ゲート
