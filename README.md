# BB_skills

Brain Bulking の現役 Claude Code skill だけを置く軽量リポジトリです。

現在残す skill は次の3つに絞っています。

| Skill | 役割 |
|---|---|
| `tiktok-speed` | TikTok向けの高速制作。タイトル案、6〜7枚台本、画像生成プロンプト、まとめ表、キャプションを作る |
| `bb-note-threads` | Note記事とThreads投稿の制作・展開 |
| `substack-fit-writer` | Substack向け。Note / memo / 記事 / full set を作る |

## セットアップ

```bash
cd /Users/asyuyukiume/Projects/BB_skills
chmod +x setup.sh
./setup.sh
```

`~/.claude/skills` に上記3skillだけを symlink 登録します。過去にこのリポジトリから登録した旧skillがあれば、`setup.sh` が解除します。

## 使い方

### TikTok高速版

```text
/tiktok-speed テーマ
```

### Note / Threads

```text
/bb-note-threads
```

`note-mcp` が登録済みで認証済みの場合、Note記事は Notion 保存後に note.com の下書きへ自動保存します。記事本文の導入直後に `[TOC]` を入れ、note.com 側で H2/H3 から目次を自動生成します。

公開は自動では行いません。ユーザーが明示的に「公開して」と指示した場合だけ公開します。

### Substack

```text
/substack-fit-writer
```

## 運用方針

Brain Bulking の戦略・進捗・投稿ログ・Substack運用方針の正本は、Obsidian vault 側に集約します。

```text
/Users/asyuyukiume/Brain Bulking/BrainBulking
```

このリポジトリは、実行用 skill の最小セットとして扱います。
