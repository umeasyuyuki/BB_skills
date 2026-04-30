# bb-line-oc-morning

BB（Brain Bulking）LINE オープンチャット「サイエンスベースフィットネス@Brain Bulking」の毎朝発信用コンテンツを生成する Claude Code スキル。

## 何をするか

毎朝、LINE OC に投稿する候補を **7本** 自動生成し、Notion「投稿管理」DB に保存する。  
人間は朝に Notion を開いて1本選び、コピペで LINE OC に投稿する。

## 出力の内訳

| カテゴリ | 本数 | ソース |
|---|---:|---|
| Tips（科学的根拠ベース） | 3 | PubMed / ACSM / NSCA / Examine.com / Reddit r/fitness |
| News（直接系） | 3 | Google News / 日経ヘルスケア / 健康産業新聞 |
| News（間接系：相場・規制） | 1 | Bloomberg / 日経新聞 |
| **合計** | **7** | |

## LINE フォーマット

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

詳細: [references/line-format-spec.md](references/line-format-spec.md)

## 使い方

### 通常モード（毎朝7本）

```
/bb-line-oc-morning
```

7投稿（Tips 3 + News 直接3 + News 間接1）を Notion に一括保存。  
**自動実行（cron 5:30）はこのモード固定**。

### テーマ指定モード（深掘り1本）

```
/bb-line-oc-morning "クレアチンの最新メタ分析"
/bb-line-oc-morning "GLP-1薬とプロテイン市場の今後"
```

引数にテーマ文字列を渡すと、そのテーマだけ深掘り（5〜6ラウンド検索）して **1本** Notion に保存。  
カテゴリ（tips / news-direct / news-indirect）はテーマ内容から自動判定。  
重複チェックは警告のみで継続（ユーザー意図優先）。

### 自動実行（cron）

```
/schedule "30 5 * * *" /bb-line-oc-morning
```

毎朝 5:30 JST に通常モードで起動 → 5:37 頃に Notion へ7投稿完成。

### オプション（両モード共通）

| フラグ | 動作 |
|---|---|
| `--dry-run` | Notion 保存をスキップ、標準出力のみ |
| `--skip-research` | 直近のリサーチ結果を再利用 |

## 保存先

- Notion DB: 投稿管理
- URL: https://www.notion.so/35171b5aad9a80659acdfd55d62e4b78
- data_source_id: `35171b5a-ad9a-80ce-b1a2-000b8947c6b9`

DB プロパティ:
- 名前（title）
- 日付（date）
- 投稿済みチェック（checkbox）— 投稿後に人間がオン

## 他スキルとの関係

| スキル | 役割 | LINE OC URL |
|---|---|---|
| **bb-line-oc-morning（本スキル）** | LINE OC **内向け**毎朝発信 | 不要（既メンバー向け） |
| bb-note-threads | Threads / Note 外向け、LINE OC へ誘導 | 末尾に固定文で挿入 |
| contents-fullmake | TikTok カルーセル | **絶対に入れない** |

## ファイル構成

```
bb-line-oc-morning/
├── SKILL.md                       # メイン手順（5 Phase）
├── README.md                      # このファイル
└── references/
    ├── line-format-spec.md        # LINE フォーマット詳細
    ├── source-priority.md         # ソース優先順位
    ├── compliance-light.md        # 薬機法簡易チェック
    └── workflow-spec.md           # Phase 詳細・API 仕様
```

## 重複防止

過去30日のタイトルを Phase 0 で取得し、Phase 1 のリサーチ時に類似度70%以上のテーマを除外。

## 薬機法

LINE OC はクローズドだが、効果断定（「痩せる」「筋肉がつく」等）は媒体問わず NG。  
詳細: [references/compliance-light.md](references/compliance-light.md)

## トラブルシューティング

| 症状 | 対応 |
|---|---|
| Phase 1 で7本揃わない | `references/source-priority.md` の「ネタが枯渇したときの逃げ道」を参照 |
| Notion 保存失敗 | `output/<YYYYMMDD>/` にバックアップ保存される |
| Red 判定が出続ける | テーマ自体の見直し、または手動修正待ち |

## 依存スキル

- `tiktok-fit-compliance-check`（薬機法ロジックを軽量参照）
- `research-dispatcher`（gemini → codex → claude のフォールバック制御）

## 開発時の注意

- SKILL.md 上限: 250 行 / 12 KB
- references/*.md 上限: 500 行 / 30 KB
- 改修後に必ず `../scripts/check_skill_size.sh bb-line-oc-morning` を実行
