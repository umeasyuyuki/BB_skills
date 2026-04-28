---
name: bb-note-threads
description: BB（Brain Bulking）専用のテキスト媒体オーケストレーター。タイトル投入1つで、Threads投稿（要点・抽象）とNote記事（深掘り）を並列生成し、LINEオープンチャットへの誘導文付きでNotion保存まで完結。TikTokカルーセルとは独立した「Threads → Note → LINE OC」動線を作るためのスキル。
---

<!--
このファイルはコア手順のみ。詳細仕様は references/ 配下に分離。
上限: 250 行 / 12 KB（CONTRIBUTING.md 参照）。
1改修ごとに +30 行を超える追加は references/ への切り出しを検討すること。
肥大化チェック: ../scripts/check_skill_size.sh bb-note-threads を改修後に必ず実行。
-->

# BB Note × Threads オーケストレーター

## 概要

タイトル文字列1つを入口に、Threads投稿とNote記事を並列生成し、両方にLINEオープンチャットへの誘導を埋め込んでNotion保存する。TikTokカルーセル生成（contents-fullmake）とは完全に独立した、テキスト媒体専用の動線を構築するためのスキル。

動線設計:

```
Threads（要点・抽象、500-700字）
   ↓ Note URL リンク
Note（深掘り、2500-3500字）
   ↓ LINE OC URL + 「なぜ最新トレンドが必要か」
LINE オープンチャット（コミュニティ化）
```

## 固定プロファイル

- KPI: Threads エンゲージメント率、Note への遷移率、LINE OC 加入数
- コンセプト: 筋トレ中・上級者向け。コンディショニングや努力を最大化するための栄養学・ヘルスケア情報。情弱ビジネスを終わらせる側
- 対象: 20-40 代男性、筋トレ中級以上
- 文章レベル: 高校生が理解できる日本語
- 口調: 関西弁レベル 2（バランス型）。情熱が見える怒りをツッコミ系の関西弁で表現。事実で殴り、思想を叫ぶ。「〜やで」「〜ねん」「ほな」「せやから」等を自然に使う
- 出力: Markdown × 2（Threads / Note）
- 媒体差別化: Threads は要点・抽象・短文、Note は深掘り・SEO・長文
- 関西弁の使い分け: Threads = 全文関西弁レベル 2 / Note = 地の文標準語 + 主張・体験談で関西弁ハイブリッド / L2-L4 固定文 = 標準語維持

## BB の思想

- 敵: 「知らない」につけ込んで金を抜く奴ら全員
- 信念: 正しい情報はタダで届けられる。俺らが証明する
- 姿勢: 京大院生と薬剤師が、論文と法律で殴る
- 宣言: 「情弱ビジネスを、終わらせる。」
- LINE OC コンセプト: 「日本最先端を本気で目指す、完全無料のフィットネス × ヘルスケアコミュニティ」

## 起動フロー

引数の数で分岐する。

| 呼び出し方 | 動作 |
|---|---|
| `/bb-note-threads` | 対話モード：タイトル質問 → フルフロー |
| `/bb-note-threads "タイトル"` | タイトル即採用 → フルフロー |

カテゴリは 5 種：compare / ingredient / entertainment / debunk / discovery（contents-fullmake と共通、L1 誘導文の参考プール選択に使う）

## Phase 0: タイトル受領

投入されたタイトル文字列をそのまま採用する。タイトル評価フローは持たない（contents-fullmake の Phase 1.5 とは異なる）。

サブステップ:

1. タイトル文字数チェック（13〜30字推奨、超過時は警告のみ）
2. テーマカテゴリ自動判定（5 種）→ L1 誘導文の参考プール選択に使用
3. 確定タイトルとカテゴリを Phase 1 / Phase 2 に渡す

詳細: `references/workflow-spec.md` の「Phase 0」参照

---

## Phase 1: リサーチ（researcher 単独）

`tiktok-fit-research` を `researcher` エージェントとして起動し、科学的根拠・PubMed・公式データを収集する。差別化軸の抽出も researcher の調査範囲に統合（旧 competitor-analyst は廃止）。

| name | 担当スキル | 役割 |
|---|---|---|
| `researcher` | `tiktok-fit-research` | 科学的根拠 + 既存情報との差別化軸抽出 |

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

| 型 | 親 | 本体リプ | 誘導リプ | 合計 |
|---|---:|---:|---:|---:|
| ⚪選系 / ランキング系 | 1 | 1 | 1 | 3 |
| 体験談型 / 対比型 | 1 | 2 | 1 | 4 |

各ポスト 200-300 字。誘導リプ（最終）に LINE OC URL と Note URL を併記する。本体ポストには URL を入れない。

### 両エージェント共通の必須要素（誘導リプ / Note 末尾に組み込む）

- **L1 テーマ連動フック**（記事ごとに新規生成、`references/line-oc-templates.md` の参考プールを参照）
- **L2 ポジショニング**（固定文）: 「京大院生と薬剤師が、日本最先端を本気で目指す、完全無料のフィットネス × ヘルスケアコミュニティ」
- **L3 変化訴求**（固定文）: Threads 圧縮版「成分表を見て、体に必要なものを判断できるように。」/ Note 通常版「読んでいるだけで、成分表を見て体に必要なものを自分で判断できるレベルになる。」
- **L4 ベネフィット + URL**（固定）: 「毎朝、最新ニュースを翻訳して配信中」+ LINE OC URL +「サイエンスベースフィットネス@Brain Bulking」

Threads 誘導リプには Note URL プレースホルダ（`【★Note URL を貼る★】`）も併記する。Note 公開後、Threads 投稿時に手動で URL 差し替え。

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

- L2-L4 が一字一句固定文と一致しているか
- L1 が記事テーマと連動しており、コピペテンプレートになっていないか
- LINE OC URL（`https://line.me/ti/g2/lmmjCh0V39BIgClQxQmsm4Hb-G8Hb7VFsnVOuw`）が完成形で直書きされているか
- 「サイエンスベースフィットネス@Brain Bulking」がチャット名として明記されているか
- AI っぽい曖昧表現（「ケースバイケース」「一概には」等）が混入していないか

---

## TikTok との分離原則

- **TikTok カルーセル**には LINE OC URL を**絶対に入れない**（contents-fullmake/references/line-oc.md と整合）
- **本スキル（Threads / Note）**にだけ LINE OC URL を完成形で直書きする
- TikTok 用台本生成が必要な場合は `contents-fullmake` を使う（こちらは TikTok カルーセル専用に縮退済み）

---

## エラー時の挙動

- Phase 1 で researcher が失敗した場合: 中断、ユーザーにエラー報告
- Phase 2 で writer が失敗した場合: もう一方の writer 結果は保持、失敗側のみリトライ
- Phase 3 で Red 判定が 2 回続いた場合: ユーザーに手動修正を依頼
- Phase 4 で Notion 保存失敗時: ローカルファイルに `output/<timestamp>/` でバックアップ保存

---

## 参考ファイル

- `references/workflow-spec.md` — Phase 詳細・エージェント通信仕様
- `references/kansai-tone.md` — **関西弁トーンガイド（共通、必読）**
- `references/threads-style.md` — Threads 文体ガイド（ツリー構成・4 型）
- `references/note-style.md` — Note 文体ガイド（ハイブリッド関西弁）
- `references/line-oc-templates.md` — LINE OC 誘導文テンプレ（L1 参考プール + L2-L4 固定文）
- `references/output-spec.md` — 出力フォーマット定義
- `references/notion-publishing.md` — Notion 保存仕様
- `references/quality-gates.md` — セルフチェック・薬機法ゲート
