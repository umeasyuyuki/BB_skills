---
description: 筋太郎のSubstack Noteを生成し、必要ならMCP/API経由で投稿する
argument-hint: "テーマ、または 投稿/下書き/案だけ など"
---

# Substack Note

筋太郎のSubstack内短文投稿 `Note` を作成する。note.comの記事ではない。

入力:

```text
$ARGUMENTS
```

## 参照する文脈

必ず必要最小限で確認する。

- `/Users/asyuyukiume/Projects/BB_skills/docs/obsidian-substack/Substack 運用OS.md`
- `/Users/asyuyukiume/Projects/BB_skills/docs/substack-execution-playbook.md`
- `/Users/asyuyukiume/Projects/BB_skills/docs/obsidian-substack/Substack 制作ボード.md`
- `/Users/asyuyukiume/Projects/BB_skills/docs/obsidian-substack/Substack 公開ログ.md`

## 文体

- 投稿者名は `筋太郎　〜フィットネスとAI大好きマン〜`
- 一人称は `僕`
- 大学院で腸内細菌の研究をしながらソフトウェアエンジニアをしている個人として書く
- フィットネス、栄養、サプリ、健康情報を、読者と一緒に考える温度感にする
- 敬語ベース
- 真面目な注意書き以外は文末を `！` 寄りにする
- `🔥` `💪` は自然に使ってよい
- 複数人運営、公式メディア、監修チーム感は出さない
- 思想を押しつけない。「それって自分に必要？」を一緒に考える
- 「成分表めくれ」と命令しない

## Noteの基本仕様

- 100〜300字を基本にする
- 1投稿1テーマ
- 読者が返しやすい問いで終える
- サプリや健康効果は断定しない
- 体験談、迷い、気づきから入る
- AI活用の話は、筋トレ/栄養/健康情報整理につながる場合だけ扱う

## 安全ゲート

以下を含む場合は自動投稿しない。案だけ出して確認を求める。

- 疾患名
- 医薬品
- 妊娠/授乳
- 未成年
- 競技規則/ドーピング
- 「治る」「改善する」に近い健康主張
- 特定商品の強い購入推奨

品質スコア85点以上なら自動投稿してよい。ただし、ユーザーが「案だけ」「下書きだけ」と言った場合は投稿しない。

## 実行フロー

1. `$ARGUMENTS` からテーマ、投稿するかどうか、時間指定の有無を読む。
2. テーマが空なら、`Substack 制作ボード.md` の当日枠または次の未投稿Note候補から選ぶ。
3. Note案を3本作る。切り口は `体験談型`、`問い型`、`ミニ解説型` を基本にする。
4. もっとも良い案を1本選び、品質ゲートを通す。
5. ユーザーが投稿を求めている場合はMCP/API経由で投稿する。
6. 投稿後、`Substack 公開ログ.md` と `Substack 制作ボード.md` を更新し、Obsidian vaultにも同期する。

## 投稿方法

標準MCPの `post_note` が403になる場合がある。ブラウザ操作ではなくAPI経由を優先する。

成功実績のある方式:

- Chrome Profile 4のCookieを利用
- `https://substack.com/api/v1/comment/feed` にPOST
- Chrome相当ヘッダーを付与
- `Origin: https://substack.com`
- `Referer: https://substack.com/home`

投稿成功時は必ず以下を記録する。

- 投稿日時
- Note本文の短いテーマ
- `note_id`
- Note URL
- CTA
- 投稿手段

## 出力

投稿しない場合:

```markdown
## Note案

### 推奨案
...

### 代替案
...

## 投稿前チェック
- 品質スコア:
- 自動投稿可否:
- 注意点:
```

投稿した場合:

```markdown
投稿しました。

- note_id:
- URL:
- ログ:
```
