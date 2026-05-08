# Skill Registry

更新日: 2026-05-07

`BB_skills` は Brain Bulking の現役 skill だけを置く軽量リポジトリに整理した。

## Active Skills

| Skill | Status | 役割 |
|---|---|---|
| `tiktok-speed` | active | TikTok高速制作。タイトル案、6〜7枚台本、画像生成プロンプト、まとめ表、キャプションを作る |
| `bb-note-threads` | active | Note記事とThreads投稿の制作・展開 |
| `substack-fit-writer` | active | Substack向け。Note / memo / 記事 / full set を作る |

## Removed

以下は現行運用から外した。

- `contents-fullmake`
- `bb-business-strategist`
- `fitness-trend-researcher`
- `line-stamps`
- `archive`
- `tiktok-fit-*` 系の部品skill
- `tiktok-fit-reel-renderer`
- `tiktok-fit-slide-renderer`
- `.claude/worktrees`

## Rule

- 新しく追加する skill は、Brain Bulking の現行運用で直接使うものだけにする。
- 依存環境、生成物、Claude worktree、キャッシュはリポジトリに入れない。
- 戦略、進捗、投稿ログ、Substack運用方針は Obsidian vault を正本にする。
