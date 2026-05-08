---
description: 筋太郎のSubstack Noteを短文作成し、必要なら投稿する
argument-hint: "テーマ 投稿して/案だけ など"
---

# Substack Note Shortcut

これは `/substack-note` の短縮版。Substack内の短文 `Note` を作成する。note.comの記事ではない。

入力:

```text
$ARGUMENTS
```

## 実行

`.claude/commands/substack-note.md` の手順を読み、同じ品質ゲートと投稿手順で実行する。

特に守ること:

- 投稿者は `筋太郎　〜フィットネスとAI大好きマン〜`
- 一人称は `僕`
- 敬語ベース、温度高め、真面目な注意書き以外は `！` 寄り
- `🔥` `💪` を自然に使う
- 複数人運営、公式感、監修チーム感は出さない
- 思想を押しつけず、読者と一緒に考える
- 健康/サプリ効果は断定しない
- ユーザーが「投稿して」と言ったら、品質ゲート後にMCP/APIで投稿する
- 「案だけ」「下書きだけ」の場合は投稿しない
- 投稿後は `Substack 公開ログ.md` と `Substack 制作ボード.md` を更新し、Obsidian vaultへ同期する

## 使い方

```text
/substa-note マグネシウムの重要性 投稿して
/substa-note プロテインを買う前に見ること 案だけ
```
