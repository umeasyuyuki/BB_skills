# ワークフロー仕様

## 入力

- 必須: `title`（タイトル文字列、13〜30 字推奨、超過は警告のみ）
タイトル評価フローは持たない（投入されたタイトルをそのまま採用）。

## カテゴリ判定（L1 誘導文の参考プール選択用）

contents-fullmake と同じ 5 種を使う:

| カテゴリ | コード名 | 例 | L1 誘導文の方向性 |
|---|---|---|---|
| 比較系 | `compare` | プロテイン A vs B | コスパ・選択判断 |
| 誤認訂正系 | `debunk` | よくある勘違い | 古い常識のアップデート |
| 成分解説系 | `ingredient` | クレアチン・アシュワガンダ等 | 成分表リテラシー |
| エンタメ系 | `entertainment` | 有名選手の食事 | 知識の楽しさ |
| 発見解剖系 | `discovery` | 異常事例の科学的分解 | 論文〜現場のラグ |

カテゴリは Phase 0 でオーケストレーターが自動判定する（タイトル文字列のキーワードマッチング）。判定信頼度が低い場合（< 60%）はユーザーに確認する。

## エージェント実行フロー

```
┌──────────────────────────────────────────────────────────┐
│  オーケストレーター（メインエージェント）                  │
│  タイトル受取 → カテゴリ判定 → Phase 1 起動                │
└──────────────┬───────────────────────────────────────────┘
               │ Phase 1（researcher 単独）
               ▼
        ┌──────────────────────┐
        │  researcher           │
        │  tiktok-fit-research  │
        │  ・科学的根拠収集     │
        │  ・PubMed/公式データ  │
        │  ・既存情報との差別化軸│
        └──────────┬───────────┘
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
```

旧 competitor-analyst は廃止（差別化軸の抽出は researcher の調査範囲に統合）。

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

## Phase 1: リサーチ（researcher 単独）

### 起動

```
Agent({name: "researcher", subagent_type: "Explore", ...})
```

### researcher への指示テンプレ

```
役割: タイトル「{title}」について、科学的根拠と差別化軸を収集する。
出力: Markdown形式のリサーチノート。
  ## 主要エビデンス
  - 作用機序 / 効果
  - 引用文献 5-8 件（PubMed ID 必須）
  - 反対意見・批判的観点も含める

  ## 既存情報との差別化軸
  - テーマで流通している主張・常識・通説 2-3 点
  - それを覆す or 補強する独自角度

  ## 薬機法注意点（サプリ・栄養テーマの場合）
```

マージ結果のフォーマット:

```markdown
# 確定タイトル: {title}
# カテゴリ: {category}

## 主要エビデンス
（researcher の出力から、引用付きで 5-8 件）

## 独自角度
（researcher の出力から、既存情報との差別化軸）

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
役割: タイトル「{title}」に基づき、Threads 投稿（500-700字）を生成する。
入力: Phase 1 マージ結果（タイトル、カテゴリ、エビデンス、独自角度）
文体ガイド: references/threads-style.md
出力構造: references/output-spec.md の「Threads 末尾構造」に厳密に従うこと。

必須要素:
- 本文（要点・抽象、Note への興味を引く）
- Note URL プレースホルダ（【★Note URL を貼る★】）
- L1 テーマ連動フック（references/line-oc-templates.md の参考プールを基にして、記事ごとに新規生成）
- L2-L4 固定文（references/line-oc-templates.md の固定文を一字一句変えない）
- LINE OC URL: https://line.me/ti/g2/lmmjCh0V39BIgClQxQmsm4Hb-G8Hb7VFsnVOuw（完成形で直書き）
- チャット名「サイエンスベースフィットネス@Brain Bulking」を末尾に明記

セルフチェック: 出力前に references/quality-gates.md の 12 項目を必ず実行すること。
```

### note-writer への指示テンプレ

```
役割: タイトル「{title}」に基づき、Note 記事（2500-3500字）を生成する。
入力: Phase 1 マージ結果（タイトル、カテゴリ、エビデンス、独自角度）
文体ガイド: references/note-style.md
出力構造: references/output-spec.md の「Note 末尾構造」に厳密に従うこと。

必須要素:
- 導入（手紙トーン、読者の課題を言語化）
- 本論 3-5 セクション（H2 見出し、各セクション 400-700 字）
- まとめ（結論を 3 行以内で言い切る）
- LINE OC 誘導フル版（L1 連動 + L2-L4 固定、references/line-oc-templates.md 参照）
- 脚注 5-8 件（PubMed ID または公式情報源）

セルフチェック: 出力前に references/quality-gates.md の 12 項目を必ず実行すること。
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

## エラー処理

| 発生箇所 | 動作 |
|---|---|
| Phase 1 で researcher が失敗 | 中断、ユーザーにエラー報告 |
| Phase 2 で writer が失敗 | もう一方の writer 結果は保持、失敗側のみリトライ（最大 2 回） |
| Phase 3 で Red 判定が 3 回続く | ユーザーに手動修正を依頼 |
| Phase 4 で Notion 保存失敗 | ローカルファイル `output/<timestamp>/` にバックアップ保存、ユーザーに通知 |

---

## 出力ディレクトリ構造（バックアップ用）

```
output/
└── <YYYY-MM-DD-HHMM>/
    ├── research-merged.md
    ├── threads.md
    ├── note.md
    ├── compliance-report.md
    └── notion-pages.json   # 保存済みページ URL を記録
```

環境変数 `BB_NOTE_THREADS_OUTPUT_DIR` で出力先を上書き可能（既定値は worktree 直下の `output/`）。
