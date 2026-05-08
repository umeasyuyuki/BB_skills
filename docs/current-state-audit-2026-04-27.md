# BB_skills 現状把握メモ

作成日: 2026-04-27

## 目的

このリポジトリは現在、Brain Bulking のコンテンツ制作向け Claude Code skill 集として使われている。

今後はそれだけでなく、BB の活動全体を管理する基盤に広げる想定:

- skills 管理
- 進捗管理
- ドキュメント管理
- SNS 戦略設計
- マネタイズ戦略設計
- BB Checker などのシステム開発

このメモでは、現時点の構成、`/Users/asyuyukiume/life-manager` 側にある BB 戦略、形骸化候補、最初に整理すべき論点をまとめる。

## 確認した主な資料

- `README.md`
- すべての top-level `*/SKILL.md`
- `setup.sh`
- `.gitignore`
- `contents-fullmake/` 配下の references / scripts
- `/Users/asyuyukiume/life-manager/world/projects/brain-bulking/README.md`
- `/Users/asyuyukiume/life-manager/world/projects/brain-bulking/strategy.md`
- `/Users/asyuyukiume/life-manager/world/projects/brain-bulking/content-strategy-playbook.md`
- `/Users/asyuyukiume/life-manager/world/projects/brain-bulking/bb-monetization-strategy.md`
- `/Users/asyuyukiume/life-manager/world/projects/brain-bulking/bb-checker-business-plan.md`
- `/Users/asyuyukiume/life-manager/world/projects/brain-bulking/tiktok-workflow.md`

## リポジトリの現状

### 存在しているもの

- `SKILL.md` を持つ top-level skill が 14 個。
- 中核は `contents-fullmake`。テーマ入力から複数媒体の投稿生成まで担う。
- 調査、競合分析、カルーセル台本、薬機法チェック、Notion 保存、画像生成、リール生成、TikTok 分析の skill がある。
- `tiktok-fit-reel-renderer/remotion-project` に Remotion 実装がある。
- `line-stamps/` は BB skill というより別プロジェクトに見える。
- `Research_report/` に過去の調査レポートがある。
- `contents-fullmake/scripts/` に Notion 自動実行系の素材がある。

### Git / リポジトリ衛生面の所見

- 作業ツリーはすでに dirty。主な変更箇所は `contents-fullmake/` と `tiktok-fit-notion-publisher/`。
- 未追跡または新規追加候補として `.claude/`、`fitness-trend-researcher/`、`line-stamps/`、`contents-fullmake/scripts/` などがある。
- `tiktok-fit-reel-renderer/remotion-project/node_modules` が git 管理下に入っている。確認時点で tracked `node_modules` パスは 11,249 件。
- ローカル生成物のサイズ:
  - `tiktok-fit-reel-renderer/remotion-project/node_modules`: 213 MB
  - `line-stamps/.venv`: 438 MB
  - `line-stamps/output`: 1.6 MB
- `.gitignore` は `node_modules`、`.venv`、生成メディア、広めの output/log を十分に除外できていない。
- `setup.sh` は top-level ディレクトリをすべて `~/.claude/skills` に symlink するため、`Research_report`、`line-stamps`、`scripts` のような非 skill ディレクトリも登録されうる。

## life-manager 側の BB 戦略

### 現在の BB ポジション

BB は単なる中立的なフィットネス情報アカウントではなく、思想型メディアへ移行済み。

- ブランドポジション: `筋トレ界の空想科学読本`
- 方針転換: 情報提供型 -> 思想発信型
- 敵: 「知らない」につけ込んで金を抜く構造
- 宣言: `情弱ビジネスを、終わらせる。`
- 一人称: `俺ら` / `俺たち`
- 信頼の根拠: 京大研究者視点 + 薬剤師/法規視点 + AI/システム開発力

### 事業目標

- TikTok: 2026-12 までに 10,000 フォロワー
- X: 2026-12 までに 3,000 フォロワー
- 有料コミュニティ: 2026-12 までに 30 人
- サプリ案件: 2026-12 までに 1 件以上
- 直近の優先収益源: 有料コミュニティ。BB Checker は収益とコミュニティ導線のハブ。

### マネタイズ柱

life-manager 側では 8 つの収益源が定義されている。

1. BB 成分チェッカー
2. アフィリエイト
3. note 有料記事
4. X 収益化
5. 案件 / 企業タイアップ
6. TikTok ライブギフト
7. 有料 Discord コミュニティ
8. TikTok Creativity Program

現在のこの repo は、コンテンツ制作には強いが、収益化実行・進捗管理・事業開発の管理層はまだ薄い。

## 現在のシステム構造

### 強い中核

`contents-fullmake` は現時点で最重要の orchestration skill。

担当範囲:

- カテゴリ自動判定
- リサーチ
- 競合分析
- タイトル生成 / 評価
- カルーセル、Note、Threads 生成
- 薬機法チェック
- Notion 保存
- 画像生成フロー
- `--auto` / Notion ポーリング運用

BB の投稿制作フローの入口としてはかなり強い。

### 足りていない管理層

- repo 内に明示的な進捗管理レイヤーがない。
- BB 戦略の正本は `life-manager` 側にあり、この repo に同期されていない。
- skill のライフサイクル管理表は追加済み。active / stale の境界は `docs/skill-registry.md` と `docs/skill-triage-2026-04-27.md` で管理する。
- BB Checker、アフィリエイト、コミュニティ、案件営業などのマネタイズ実行 backlog がない。
- README はまだ「TikTok フィード投稿自動生成 skill 集」という説明が中心。
- 一部 docs は旧称 `tiktok-fit-feed-orchestrator` を参照しているが、現在の入口は `contents-fullmake`。

## 形骸化・ズレ候補

詳細は `docs/skill-registry.md` に記載。

高確度で確認すべきものとして洗い出し、2026-04-27 に一部 archive 済み:

- `archive/skills/tiktok-fit-skill-builder`: 旧トーン、旧カテゴリ、8-15 枚構成など、現在の思想型 BB とズレている。
- `archive/skills/tiktok-fit-insta-single`: 旧来の中立的専門家トーンが残り、`contents-fullmake` との接続も弱い。
- `archive/skills/tiktok-fit-trend-research` と `fitness-trend-researcher`: 目的が大きく重複。旧版は archive 済み。
- `tiktok-fit-reel-renderer`: SKILL では `/Users/asyuyukiume/Projects/Reel-movie` を参照しているが、repo 内には別の `remotion-project` がある。実行パスの整合が必要。
- `archive/skills/tiktok-fit-slide-image-generator`: `contents-fullmake` Phase 5 の Codex/Pillow 画像生成方針と重複気味。
- `README.md`: X 投稿と Threads 投稿のズレ、外部 skill `note-writer` の扱い、旧称参照などが残っている。

## 推奨する管理モデル

Claude Code skill の互換性を優先し、top-level skill ディレクトリはすぐには動かさない。

その上で、管理ドキュメントを追加して repo の役割を広げる。

- `docs/skill-registry.md`: skill の状態管理
- `docs/current-state-audit-YYYY-MM-DD.md`: 定期的な現状把握
- `docs/strategy/`: BB 戦略の正本または life-manager からの同期版
- `docs/progress/`: 週次進捗、意思決定、ブロッカー、次アクション
- `docs/monetization/`: BB Checker、アフィリエイト、コミュニティ、案件設計
- `docs/system/`: アプリ、Notion schema、自動化、レンダリング基盤の設計

## 最初にやるべき整理

1. skill registry を作り、全 skill に `core` / `active` / `supporting` / `experimental` / `legacy` / `archive-candidate` を付ける。
2. repo 衛生面を直す。
   - `node_modules`、`.venv`、生成 output、log、ローカル media を ignore
   - `setup.sh` が非 skill を登録しないようにする
   - すでに tracked な `node_modules` をどう扱うか決める
3. 命名のズレを揃える。
   - `tiktok-fit-feed-orchestrator` -> `contents-fullmake`
   - X 投稿 vs Threads 投稿
   - 外部 skill `note-writer` の扱い
4. trend research の canonical を決める。
   - Gemini CLI + Notion 自動保存を優先するなら `fitness-trend-researcher`
   - 旧 `tiktok-fit-trend-research` は統合または legacy 化
5. stale skill を現行戦略へ寄せる。
   - team voice
   - 思想型メディア
   - 現在の 9-12 枚カルーセル
   - 有料コミュニティ / BB Checker / LINE OpenChat 導線
6. 進捗管理を追加する。
   - BB 週次 status
   - マネタイズ backlog
   - skill 保守 backlog
   - システム開発 backlog

## 次の一手

まずは以下の repo-level docs を揃える。

1. `docs/skill-registry.md`
2. `docs/progress/weekly-status.md`
3. `docs/monetization/bb-checker-roadmap.md`
4. `docs/strategy/canonical-bb-strategy.md`

その後、最初の小さな cleanup として `.gitignore`、`setup.sh`、README の命名ズレを直す。

投稿生成ロジック本体は、active / legacy の境界が決まるまで大きく触らない。
