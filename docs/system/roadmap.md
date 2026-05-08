# BB System Roadmap

作成日: 2026-04-27

## 目的

BB の活動を、属人的な投稿制作から再現性のあるシステム運用へ移行する。

## 現在のシステム領域

| 領域 | 現状 | 次の整理 |
|---|---|---|
| 投稿制作 | `contents-fullmake` に集約 | 部品 skill の扱いを固定する |
| 事業戦略 | `bb-business-strategist` を追加 | マネタイズ・ロードマップ・意思決定を docs と接続 |
| Notion 保存 | `tiktok-fit-notion-publisher` | DB schema と保存対象を明文化 |
| 画像生成 | `tiktok-fit-slide-renderer` + Codex 画像生成 | canonical flow を README 化 |
| リール動画 | `tiktok-fit-reel-renderer` | 実行パスと依存関係を修正 |
| リサーチ | `fitness-trend-researcher` optional | 使う頻度に応じて skill か docs にする |
| 進捗管理 | docs 追加開始 | 将来的に Notion DB と連携 |
| BB Checker | 企画段階 | MVP 設計から開始 |

## 優先タスク

1. setup 対象を現役 skill に限定する。
2. archive skill を Claude Code 登録対象から外す。
3. tracked `node_modules` の扱いを整理する。
4. reel renderer の project path を repo 内に揃える。
5. BB Checker の MVP 技術設計を作る。

## Repository Hygiene

直近で必要:

- `node_modules` を ignore する
- `.venv` を ignore する
- generated output / logs を ignore する
- `setup.sh` は allowlist 方式にする
- `archive/skills` は登録対象にしない

## 将来の理想構成

```text
contents-fullmake/          # 投稿制作入口
tiktok-fit-reel-renderer/   # 動画制作
docs/                       # 戦略・進捗・収益化・システム管理
archive/skills/             # 非現役 skill
Research_report/            # 調査レポート保管
```

## BB Checker MVP メモ

まだ実装前。想定:

- Cloudflare Workers / Pages
- D1 or Supabase
- ルールベースのスコアリング
- AI は詳細分析コメントのみ
- 初回無料、以降クレジット or 会員化

詳細は `docs/monetization/roadmap.md` から個別設計に切り出す。
