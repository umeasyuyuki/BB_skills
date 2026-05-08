# ワークフロー仕様

## 入力

- 必須: `title`（タイトル文字列、13〜30 字推奨、超過は警告のみ）
- 任意: `--no-competitor`（競合分析を省略する軽量モードフラグ）

タイトル評価フローは持たない（投入されたタイトルをそのまま採用）。

## カテゴリ判定（切り口調整用）

contents-fullmake と同じ 5 種を使う:

| カテゴリ | コード名 | 例 | Threads / Note の方向性 |
|---|---|---|---|
| 比較系 | `compare` | プロテイン A vs B | コスパ・選択判断 |
| 誤認訂正系 | `debunk` | よくある勘違い | 古い常識のアップデート |
| 成分解説系 | `ingredient` | クレアチン・アシュワガンダ等 | 成分表リテラシー |
| エンタメ系 | `entertainment` | 有名選手の食事 | 知識の楽しさ |
| 発見解剖系 | `discovery` | 異常事例の科学的分解 | 論文〜現場のラグ |

カテゴリは Phase 0 でオーケストレーターが自動判定する（タイトル文字列のキーワードマッチング）。判定信頼度が低い場合（< 60%）はユーザーに確認する。

## エージェントチーム実行フロー

```
┌──────────────────────────────────────────────────────────┐
│  オーケストレーター（メインエージェント）                  │
│  タイトル受取 → カテゴリ判定 → Phase 1 起動                │
└──────────────┬───────────────────────────────┬───────────┘
               │ Phase 1（TeamCreate 並列チーム）│
               ▼                                ▼
┌──────────────────────┐     ┌──────────────────────────────┐
│  researcher           │◄───►│  competitor-analyst           │
│  tiktok-fit-research  │     │  tiktok-fit-post-competitor-  │
│                       │     │  analysis                     │
│  ・科学的根拠収集     │────►│  ・Threads/Note 競合の独自角度 │
│  ・PubMed/公式データ  │◄────│  ・盲点発見 → 追加調査依頼     │
└──────────┬───────────┘     └──────────────┬───────────────┘
           │                                │
           └───────────────┬────────────────┘
                           ▼
                ┌─────────────────────┐
                │  結果マージ＆重複除去 │
                └──────────┬──────────┘
                           │ Phase 2（2メディア並列）
                           ▼
              ┌──────────────┬──────────────┐
              │ threads-writer│  note-writer  │
              └──────┬───────┴──────┬───────┘
                     │              │
                     └──────┬───────┘
                            │ Phase 3（薬機法）
                            ▼
                  ┌──────────────────┐
                  │ compliance-check  │
                  └────────┬─────────┘
                           │ Phase 4（Notion 保存）
                           ▼
                  ┌──────────────────┐
                  │ notion-publisher  │
                  │ + paired_post_url │
                  └──────────────────┘
                           │ Phase 5（note.com 下書き）
                           ▼
                  ┌──────────────────┐
                  │ note-mcp          │
                  │ draft + preview   │
                  └──────────────────┘
```

---

## Phase 0: タイトル受領

サブステップ:

1. **入力検証**: タイトル文字列の文字数チェック（13〜30 字推奨、超過時は警告）
2. **カテゴリ自動判定**: タイトル文字列のキーワードマッチング → 5 カテゴリのいずれかにアサイン
3. **判定信頼度チェック**: < 60% の場合、ユーザーに `AskUserQuestion` で確認
4. **確定情報のパッケージ化**: `{title, category, theme_keywords[]}` を Phase 1 / Phase 2 入力として保持

カテゴリ判定キーワード例:

| カテゴリ | キーワード（例） |
|---|---|
| compare | vs、比較、ランキング、どっち、おすすめ |
| debunk | 嘘、勘違い、間違い、誤解、常識 |
| ingredient | クレアチン、プロテイン、ビタミン、成分、サプリ |
| entertainment | 〇〇選手、〇〇プロ、有名、芸能 |
| discovery | 驚異、異常、極端、〇〇 kg、〇〇 % |

詳細実装は SKILL.md の Phase 0 ロジックを参照（Phase 0 のロジックは SKILL.md 内で完結する）。

---

## Phase 1: 並列調査（research + competitor-analysis）

### 起動

```
TeamCreate({team_name: "bb-note-threads-team"})
→ Agent({name: "researcher", subagent_type: "Explore", team_name: "bb-note-threads-team", ...})
→ Agent({name: "competitor-analyst", subagent_type: "Explore", team_name: "bb-note-threads-team", ...})
```

`--no-competitor` フラグ指定時は `competitor-analyst` を起動せず、`researcher` のみ実行する。

### researcher への指示テンプレ

```
役割: タイトル「{title}」について、科学的根拠（PubMed・公式データ・査読論文）を収集する。
出力: Markdown形式のリサーチノート。
  - 主要な作用機序 / 効果
  - 引用文献 5-8 件（PubMed ID 必須）
  - 反対意見・批判的観点も含める
  - サプリ・栄養テーマの場合は薬機法上の注意点を明記
通信: 序盤で発見した「主要キーワード」「切り口」を SendMessage({to: "competitor-analyst"}) で共有すること。
```

### competitor-analyst への指示テンプレ

```
役割: タイトル「{title}」と関連キーワードで、Threads / Note / YouTube の伸びている投稿を分析し、独自角度を抽出する。
出力: Markdown形式の競合分析メモ。
  - 既存の伸びている投稿の型 3-5 件（タイトル / 訴求 / KPI 推定）
  - 既存投稿が未カバーの論点（差別化軸）
  - BB の「情弱ビジネスを終わらせる」思想と整合する切り口
通信: 盲点発見時は SendMessage({to: "researcher"}) で追加調査依頼を送ること。
```

### Phase 1 マージ仕様

両エージェント完了後、オーケストレーターが以下を実行:

1. 両エージェントの出力を受け取る
2. リサーチ結果と競合分析結果のトピック対応関係を整理する
3. 重複トピックを除去し、独自角度を明確にする
4. マージ結果を Phase 2 の入力パッケージとして構成する
5. `TeamDelete` でチームを解散する

マージ結果のフォーマット:

```markdown
# 確定タイトル: {title}
# カテゴリ: {category}

## 主要エビデンス
（researcher の出力から、引用付きで 5-8 件）

## 既存競合の型
（competitor-analyst の出力から、伸びている投稿の型 3-5 件）

## 独自角度
（マージで導出された差別化軸）

## 薬機法注意点（該当時のみ）
（researcher の出力から）
```

---

## Phase 2: 並列生成（threads-writer + note-writer）

### 起動

```
Agent({name: "threads-writer", subagent_type: "general-purpose", ...})
Agent({name: "note-writer", subagent_type: "general-purpose", ...})
```

両エージェントとも、Phase 1 のマージ結果を入力として受け取る。並列実行。

### threads-writer への指示テンプレ

```
役割: タイトル「{title}」に基づき、Threads 投稿（ツリー構成、本体 200-300 字 × N + 最終リプ 240-300 字）を生成する。
入力: Phase 1 マージ結果（タイトル、カテゴリ、エビデンス、独自角度）
文体ガイド: references/threads-style.md / references/tone-guide.md / references/domain-vocabulary.md
出力構造: references/output-spec.md の「Threads 投稿」に厳密に従うこと。

型選択（必須）:
- references/threads-patterns.md の「カテゴリ × 型マッピング」を参照
- 8 型から 2 案を提案し、フックの強い方を採用
- 出力末尾に「採用案 / 不採用案 / 採用理由」を 1-2 行ずつ記載

必須要素:
- 本文（要点・抽象、Note への興味を引く、低温の標準語 BB トーン。`俺ら` / `俺たち` は原則使わない）
- 最終リプは D-2 二段構成: Note 案内（メイン 100-150 字）+ 区切り（ーーー / 空行 2 行）+ LINE OC 匂わせ（サブ 100-150 字、references/cta-policy.md の「Threads 最終リプ」参照）
- Note URL プレースホルダ（`【★Note URL を貼る★】`）を最終リプ メイン部分に配置
- Threads 全体に `line.me`（直 URL）、`完全無料`、`日本最先端`、`ステータス`、`今すぐ参加`、`全員入って`、`👇` を入れない
- LINE OC は最終リプ サブ部分のみで「プロフィールの相談室」表現で匂わせる（直 URL 禁止）

専門用語翻訳（必須）:
- references/domain-vocabulary.md の翻訳ルールを必ず読む
- 学術略称（ACSM、PubMed、mEq/L、mOsm/L 等）は素のまま使わない
- カタカナ専門語（アイソトニック、ハイポトニック、グリコーゲン、mTORC1、MPS 等）を日常語に翻訳
- 数値・単位（%、mg、kcal、円、年）は無翻訳で残す
- 論文著者名・PubMed ID は Threads では一切出さない

セルフチェック: 出力前に references/quality-gates.md の全項目（A〜G、F は Note のみ）を必ず実行すること。
```

### note-writer への指示テンプレ

```
役割: タイトル「{title}」に基づき、Note 記事（2500-3500字）を生成する。
入力: Phase 1 マージ結果（タイトル、カテゴリ、エビデンス、独自角度）
文体ガイド: references/note-style.md / references/tone-guide.md / references/domain-vocabulary.md
出力構造: references/output-spec.md の「Note 末尾構造」に厳密に従うこと。

必須要素:
- 導入（手紙トーン、読者の課題を言語化）
- 本論 3-5 セクション（H2 見出し、各セクション 400-700 字）
- まとめ（結論を 3 行以内で言い切る）
- 関連リンク案内（references/cta-policy.md の「Note 末尾構造」参照、見出しは `## 関連リンク` で固定）
- LINE オープンチャット言及（公式OC名 + 実リンク、Threads では直 URL 禁止）
- 「個別の医療相談や診断をする場所ではありません。」の免責
- 脚注 5-8 件（PubMed ID または公式情報源）

専門用語翻訳（必須）:
- references/domain-vocabulary.md の翻訳ルールを必ず読む
- 学術略称（ACSM、PubMed 等）は本文で日常語に翻訳、原語は脚注のみ
- カタカナ専門語（アイソトニック、ハイポトニック、グリコーゲン、mTORC1、MPS 等）を本文で日常語に翻訳
- 単位（mEq/L、mOsm/L 等）を本文で mg/L、g/L、「液体の濃さ」等に変換、原単位は脚注のみ
- 論文著者名（Parr et al. 等）は本文では「ある研究では〜」と書き、著者名・PubMed ID は脚注のみ
- 数値・単位（%、mg、g、kcal、円、年）は無翻訳で残す

セルフチェック: 出力前に references/quality-gates.md の全項目を必ず実行すること。関西弁が混入していないことを E-1〜E-7、専門用語翻訳を G-1〜G-6 で確認。
```

---

## Phase 3: 薬機法ゲート

両媒体の本文を `tiktok-fit-compliance-check` に並列で渡し、Red / Yellow / Green 判定を取得する。

### リトライルール

| 判定 | 動作 |
|---|---|
| Green | そのまま Phase 4 へ |
| Yellow | 警告のみ、ユーザーに最終判断を委ねる（次の Phase 4 進行はユーザー承認後） |
| Red | writer エージェントに修正版を依頼。最大 2 回まで。3 回目 Red はユーザーに手動修正を依頼 |

修正依頼時の指示テンプレ:

```
以下の表現が薬機法上 Red 判定でした:
{違反箇所と理由}

該当箇所を修正し、表現を弱めるか、エビデンス引用形式に変更してください。
全体の論旨は維持すること。
```

---

## Phase 4: Notion 保存

`tiktok-fit-notion-publisher` を呼び出し、Threads と Note の 2 ページを順次保存する。

### 保存順序

1. **Threads ページ保存**（先）
2. **Note ページ保存**（後）
3. **paired_post_url 相互リンク書き込み**
   - Threads ページの `paired_post_url` プロパティ → Note ページ URL
   - Note ページの `paired_post_url` プロパティ → Threads ページ URL

### プロパティ仕様（必須）

| プロパティ | Threads | Note |
|---|---|---|
| `content_type` | `threads` | `note` |
| `pricing_mode` | `free` | `free` |
| `funnel_stage` | `awareness` | `engagement` |
| `paired_post_url` | Note ページ URL | Threads ページ URL |

詳細: `notion-publishing.md` 参照

---

## Phase 5: note.com 下書き保存

Notion 保存後、確定した Note 記事を note.com の下書きへ保存する。詳細は `note-com-publishing.md` 参照。

### 保存順序

1. Note 記事から note.com 投入用 Markdown を作る
2. 導入直後の `[TOC]` が単独行になっていることを確認する
3. 管理メタ情報とセルフチェック結果を削除する
4. `note_check_auth` で認証状態を確認する
5. 未認証なら `note_import_chrome_cookies(browser="chrome", profile="Profile 4", verify=true)` で `brain_bulking` の Chrome Cookie を取り込む
6. `note_create_draft` で下書き保存する
7. `note_get_preview_url` で preview URL を取得する
8. article key / preview URL / Notion Note URL を出力する

公開はこの Phase では行わない。`note_publish_article` はユーザーが「公開して」と明示した場合だけ使用する。

---

## エラー処理

| 発生箇所 | 動作 |
|---|---|
| Phase 1 で researcher / competitor-analyst が両方失敗 | 中断、ユーザーにエラー報告 |
| Phase 1 で片方のみ失敗 | 残った成果物で続行、ユーザーに警告 |
| Phase 2 で writer が失敗 | もう一方の writer 結果は保持、失敗側のみリトライ（最大 2 回） |
| Phase 3 で Red 判定が 3 回続く | ユーザーに手動修正を依頼 |
| Phase 4 で Notion 保存失敗 | ローカルファイル `output/<timestamp>/` にバックアップ保存、ユーザーに通知 |
| Phase 5 で note.com 下書き保存失敗 | Notion URL とローカルバックアップを返し、note-mcp 登録状態または Chrome の note.com ログイン状態を確認 |

---

## 出力ディレクトリ構造（バックアップ用）

```
output/
└── <YYYY-MM-DD-HHMM>/
    ├── research-merged.md
    ├── threads.md
    ├── note.md
    ├── compliance-report.md
    ├── notion-pages.json   # 保存済みページ URL を記録
    └── note-com-draft.json # note.com article key / preview URL を記録
```

環境変数 `BB_NOTE_THREADS_OUTPUT_DIR` で出力先を上書き可能（既定値は worktree 直下の `output/`）。
