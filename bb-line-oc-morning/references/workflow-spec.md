# Workflow 詳細仕様

各 Phase の入出力、エージェント仕様、Notion API 呼び出しを記述する。

---

## Phase 0: 重複チェック前処理

### 入力

なし（コマンド起動のみ）

### 処理

```
1. 今日の日付（JST）を取得
2. Notion API で投稿管理 DB を query:
   - data_source_id: 35171b5a-ad9a-80ce-b1a2-000b8947c6b9
   - filter: 日付 >= (今日 - 30日)
   - sorts: 日付 descending
   - page_size: 100
3. 結果から「名前」プロパティだけ抽出
4. 重複候補リスト（タイトル文字列の配列）として返す
```

### 出力

```json
{
  "today_jst": "2026-04-29",
  "duplicate_candidates": [
    "ホエイは20g×4回が筋合成の天井",
    "原油↑でホエイプロテインは年内に値上げ確定",
    ...
  ]
}
```

### エラーハンドリング

- API エラー（429 / 5xx）: 3回リトライ。それでも失敗なら空リストで継続（警告ログ）
- 認証エラー（401）: 中断、ユーザーにトークン確認を依頼

---

## Phase 1: リサーチ（モード別分岐）

引数の有無で分岐する。

| 引数 | 起動モード | エージェント数 | 出力本数 |
|---|---|---:|---:|
| なし | 通常モード | 3並列 | 7 |
| テーマ文字列1つ | テーマ指定モード | 1単独 | 1 |

通常モードは下記、テーマ指定モードは「Phase 1: テーマ指定モード」セクション参照。

### 通常モード: 並列リサーチ（3エージェント）

#### TeamCreate

```javascript
TeamCreate({ team_name: "bb-line-oc-research" })
```

### エージェント起動（同一メッセージ内で並列）

3つの Agent tool 呼び出しを **同一メッセージ** に含める（並列実行）。

#### tips-researcher

```javascript
Agent({
  description: "Tips 3本リサーチ",
  team_name: "bb-line-oc-research",
  subagent_type: "general-purpose",
  prompt: `
あなたは BB（Brain Bulking）の Tips リサーチャー。
科学的根拠ベースのフィットネス Tips を3本特定する。

■ 重複候補リスト（このリストと類似度70%以上のテーマは選定NG）
${duplicate_candidates}

■ 優先ソース
PubMed > ACSM > NSCA > Examine.com > Reddit r/fitness Wiki

■ 検索ラウンド（gemini-3-pro-preview で実行）
Round 1: PubMed で直近1〜3年の RCT / メタアナリシス
Round 2: ACSM / NSCA の position stand
Round 3: Examine.com の成分エビデンス整理
Round 4: Reddit r/fitness Wiki の実践者議論（出典明記が必須）

■ 出力（候補3本、各候補は次の構造）
## 候補N
- タイトル: <13〜30字、主張が一目で分かる>
- カテゴリ: tips
- 要点: 3行（1行＝1事実、句点で終わる、数値/年/対象を含む）
- アクション3本: 数字・量・タイミング込み、動詞ベース、抽象語禁止
- 一言コメント: BBトーン1行、断定/体言止め可
- 根拠 URL: 実在確認済み1〜2本
- 重複判定: PASS（重複候補リストと類似度<70%）

詳細仕様: bb-line-oc-morning/references/source-priority.md
`
})
```

#### direct-news

```javascript
Agent({
  description: "直接ニュース3本リサーチ",
  team_name: "bb-line-oc-research",
  subagent_type: "general-purpose",
  prompt: `
あなたは BB の直接ニュースリサーチャー。
フィットネス・栄養・サプリ・規制の直接系ニュースを3本特定する。

■ 重複候補リスト
${duplicate_candidates}

■ 優先ソース
Google News > 日経ヘルスケア > 健康産業新聞 > NIH ODS > 厚労省/消費者庁

■ 検索ラウンド
Round 1: Google News で「サプリメント 規制 {現在の年}」「プロテイン 新発売 {現在の年}」
Round 2: 「機能性表示食品 撤回」「健康食品 回収」
Round 3: トレンド成分（クレアチン、ベータアラニン、グルタミン等）の最新動向

■ 出力（tips-researcher と同じ構造、カテゴリは news-direct）
`
})
```

#### indirect-news

```javascript
Agent({
  description: "間接ニュース1本リサーチ",
  team_name: "bb-line-oc-research",
  subagent_type: "general-purpose",
  prompt: `
あなたは BB の間接ニュースリサーチャー。
直接フィットネスではないが、価格・供給・規制を通じて影響する話題を1本特定する。

■ 重複候補リスト
${duplicate_candidates}

■ 優先ソース
Bloomberg > 日経新聞 > 日経ヘルスケア > Reuters

■ 検索テーマ例
- 原油・乳価・農産物相場の変動 → サプリ価格への影響
- 為替・関税 → 輸入サプリの値上げ
- 物流コスト → サプライチェーン
- 他業界の規制 → 健康食品への波及

■ 出力（tips-researcher と同じ構造、カテゴリは news-indirect）

ネタが枯渇している日は「該当なし」を返してよい（Phase 2 で direct-news を1本追加して4本にする）。
`
})
```

### マージ処理

3エージェントの結果を待ち、合計7候補（または6＋追加調整）を統合。

#### TeamDelete

```javascript
TeamDelete({ team_name: "bb-line-oc-research" })
```

### Phase 1: テーマ指定モード

引数にテーマ文字列が渡された場合は、TeamCreate せず単一の `theme-researcher` エージェントを起動する。

#### カテゴリ自動判定ロジック

テーマ文字列に含まれるキーワードでカテゴリを判定する（重複時は上から優先）。

| カテゴリ | 判定キーワード例 |
|---|---|
| `news-indirect` | 原油 / 為替 / 関税 / 物流 / 乳価 / 相場 / GLP-1 / サプライチェーン |
| `news-direct` | 規制 / 値上げ / 撤回 / 回収 / 新発売 / 機能性表示 / 消費者庁 / 厚労省 / 届出 |
| `tips` | 上記いずれにも該当しない場合（科学・実践・トレーニング系のデフォルト） |

#### theme-researcher プロンプト

```javascript
Agent({
  description: `テーマ指定リサーチ: ${theme}`,
  subagent_type: "general-purpose",
  prompt: `
あなたは BB（Brain Bulking）のテーマ指定リサーチャー。
ユーザー指定のテーマについて深掘り調査し、LINE オープンチャット用の投稿候補を **1本** 生成する。

■ 指定テーマ
${theme}

■ 自動判定カテゴリ
${detected_category}  // tips / news-direct / news-indirect

■ 重複候補リスト（参考、強制除外ではない）
${duplicate_candidates}
このリストと類似度70%超の場合は警告のみで継続してよい（ユーザーが意図的に同テーマを書きたい場合あり）。

■ 検索戦略（**5〜6回ラウンド、深め**に行う）
判定カテゴリに応じて bb-line-oc-morning/references/source-priority.md の優先ソースを使う。

- tips: PubMed > ACSM > NSCA > Examine.com > Reddit r/fitness
- news-direct: Google News > 日経ヘルスケア > 健康産業新聞 > NIH ODS > 厚労省/消費者庁
- news-indirect: Bloomberg > 日経新聞 > 日経ヘルスケア > Reuters

Round 1: テーマそのものをそのまま検索（最も直接的な情報）
Round 2: テーマに関連する一次ソース（論文/公式発表）を狙う
Round 3: 反論・代替仮説・批判的レビューを探す（バランス取り）
Round 4: 最新動向（直近1〜3ヶ月）の追加検索
Round 5: 実践への落とし込み（具体的アクション材料）
Round 6（必要に応じて）: 数値・量の裏取り

■ 制約（通常モードと同一）
- URL は実在確認済みのもののみ（架空URL生成は絶対禁止）
- 1次ソースを必ず1つ含める
- 数値・年・対象を本文に含める
- **標準語で記述**（関西弁・方言禁止）
- BBトーン（断定・体言止め可）。AIっぽい曖昧表現禁止

■ 出力フォーマット（候補1本）
## 候補1
- タイトル: <13〜30字、テーマを反映した主張>
- カテゴリ: ${detected_category}
- 要点: 3行（各行 = 1事実、句点で終わる、数値/年/対象を含む）
- 一言コメント: BBトーン1行（標準語）
- アクション: 1〜3個（数字・量・タイミング込み、動詞ベース、抽象語禁止）
- 根拠 URL: 実在確認済みのURL 1〜2本

タイトルが13〜30字に収まらない場合は警告のみ出して継続。
`
})
```

#### 出力後の処理

通常モードと同じ Phase 2 → 3 → 4 を流す。差分は「処理対象が1件のみ」という点だけ。

---

## Phase 2: LINE フォーマッタ

### 入力

Phase 1 の7候補（タイトル / 要点 / アクション / 一言コメント / 根拠 URL / カテゴリ）

### 処理

各候補を `references/line-format-spec.md` の骨格テンプレートに流し込む。

### セルフチェック（出力前必須）

`SKILL.md` のセルフチェック8項目を実行。1つでも不合格なら最大2回まで自動修正、3回目は手動修正待ちにする。

### 出力

```json
{
  "posts": [
    {
      "category": "tips",
      "title": "ホエイは「20g×4回」が筋合成の天井",
      "line_text": "おはようございます！\n\nホエイは「20g×4回」が筋合成の天井\n\n・1回20gを超えると...\n...\n根拠：https://pubmed.ncbi.nlm.nih.gov/...",
      "source_urls": ["https://pubmed.ncbi.nlm.nih.gov/..."],
      "research_engine": "gemini-3-pro-preview",
      "self_check_passed": true
    },
    ...（7件）
  ]
}
```

---

## Phase 3: 薬機法簡易チェック

### 入力

Phase 2 の7投稿テキスト

### 処理

`references/compliance-light.md` のチェックリストを各投稿に適用。

### 出力

```json
{
  "results": [
    { "post_index": 0, "label": "Green", "issues": [] },
    { "post_index": 1, "label": "Yellow", "issues": ["数値が無い断定"] },
    ...
  ]
}
```

Red の場合は Phase 2 にフィードバック（最大2回）。

---

## Phase 4: Notion 保存

### 入力

Phase 3 を通過した7投稿

### 処理（並列で7ページ作成）

各投稿について `mcp__notion__API-post-page` を呼び出す。

```javascript
{
  "parent": {
    "type": "data_source_id",
    "data_source_id": "35171b5a-ad9a-80ce-b1a2-000b8947c6b9"
  },
  "properties": {
    "名前": {
      "title": [{ "text": { "content": post.title } }]
    },
    "日付": {
      "date": { "start": today_jst }
    },
    "投稿済みチェック": {
      "checkbox": false
    }
  },
  "children": [
    {
      "type": "heading_3",
      "heading_3": {
        "rich_text": [{ "text": { "content": "📌 " + categoryLabel } }]
      }
    },
    {
      "type": "code",
      "code": {
        "language": "plain text",
        "rich_text": [{ "text": { "content": post.line_text } }]
      }
    },
    {
      "type": "divider",
      "divider": {}
    },
    {
      "type": "heading_3",
      "heading_3": {
        "rich_text": [{ "text": { "content": "メタ情報" } }]
      }
    },
    {
      "type": "paragraph",
      "paragraph": {
        "rich_text": [{
          "text": {
            "content": "カテゴリ: " + post.category +
                       "\n調査エンジン: " + post.research_engine +
                       "\n生成日時: " + generated_at +
                       "\n根拠: " + post.source_urls.join(", ")
          }
        }]
      }
    }
  ]
}
```

### カテゴリラベルマッピング

| post.category | categoryLabel |
|---|---|
| tips | Tips |
| news-direct | News（直接） |
| news-indirect | News（間接） |

### エラーハンドリング

- 個別ページ作成失敗: 3回リトライ、それでも失敗なら該当投稿を `output/<YYYYMMDD>/post_N.txt` に保存
- 全7ページ成功: ユーザーに保存完了URLを報告
- 一部失敗: 成功分は通常通り、失敗分はバックアップ保存先と理由を報告

---

## 自動実行（Phase B）

### cron 登録

```javascript
mcp__scheduled-tasks__create_scheduled_task({
  name: "bb-line-oc-morning",
  schedule: "30 5 * * *",
  timezone: "Asia/Tokyo",
  command: "/bb-line-oc-morning"
})
```

### 失敗時の挙動

- cron 実行が失敗した場合、ScheduleWakeup で1時間後にリトライ
- 2回連続失敗でユーザー通知

---

## ローカル出力ディレクトリ

```
output/
└── 20260429/
    ├── posts.json          # Phase 2 出力（全7投稿の構造化データ）
    ├── post_0.txt          # 各投稿の LINE テキスト（Notion 失敗時のバックアップ）
    ├── post_1.txt
    ├── ...
    └── compliance.json     # Phase 3 結果
```

---

## 全体実行時間の目安

| Phase | 想定時間 |
|---|---:|
| 0: Notion query | 5秒 |
| 1: 並列リサーチ | 3〜5分（gemini呼び出し3並列） |
| 2: フォーマッタ | 1分 |
| 3: 薬機法チェック | 30秒 |
| 4: Notion 保存 | 10秒 |
| **合計** | **5〜7分** |

cron は朝5:30 起動 → 朝5:37 頃に Notion へ7投稿完成。人間が朝7時に開けば余裕で間に合う。
