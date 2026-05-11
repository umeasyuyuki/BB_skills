---
description: 筋太郎のSubstack Post記事を作成し、下書き作成または予約投稿まで実行する
argument-hint: "テーマ、予約日時、メール有無、下書きだけ など"
---

# Substack Post

筋太郎のSubstack長文 `Post` を作成する。Substackの `Note` ではなく、タイトル/本文/予約を持つ記事。

入力:

```text
$ARGUMENTS
```

## 参照する文脈

必ず必要最小限で確認する。

- `/Users/asyuyukiume/Projects/BB_skills/docs/obsidian-substack/Substack 運用OS.md`
- `/Users/asyuyukiume/Projects/BB_skills/docs/substack-execution-playbook.md`
- `/Users/asyuyukiume/Projects/BB_skills/docs/obsidian-substack/Substack 制作ボード.md`
- `/Users/asyuyukiume/Projects/BB_skills/docs/obsidian-substack/Substack 記事案.md`
- `/Users/asyuyukiume/Projects/BB_skills/docs/obsidian-substack/Substack 公開ログ.md`
- `/Users/asyuyukiume/Brain Bulking/BrainBulking/02_SNS/Substack 投稿原稿/`

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

## AIpreneur共感フック

SubstackにはAI発信者、AIツール好き、個人開発者、AIで仕事や発信を仕組み化したい人が多い。Postではこの層に「この人、AIツールを実際に触っている側だ」と伝わるユーモアを1箇所以上入れる。

狙いは、AIの話を無理やりねじ込むことではない。**AIツールあるあるで仲間感を作り、そこからフィットネス・栄養・ヘルスケアの判断基準へ連れていく**。

使いやすい型:

```text
AIあるある
  -> フィットネス/栄養にも同じ罠がある
  -> だから今回の判断基準はここ
```

例:

- プロンプトが雑だと出力が荒れるように、食事記録も入力が雑だと判断がズレる
- AIに丸投げするとたまに変な答えが返ってくるように、サプリ選びも「何のために飲むか」が曖昧だと迷子になる
- 「とりあえず全部Notionに入れたら勝ち」と思って散らかる感じは、健康情報のブックマークにも似ている
- 画像生成AIが謎の文字を生むように、パッケージの健康っぽい言葉も雰囲気だけで読めてしまう
- Claudeに長文を投げすぎて要点がぼやけるように、成分表も全部見ようとすると優先順位を見失う

禁止:

- 「AIすごい」「AIで効率化できます」だけで終わる
- 本文テーマと関係ないAI雑談を差し込む
- 技術自慢、ツール名羅列、プロンプト芸に寄せすぎる
- 目的関数、RAG、ベクトルDBなど、日常会話で使わない専門語を比喩の中心にする
- フィットネス読者を置いていく専門用語だけの内輪ノリ

理想:

- AI好きが少し笑う
- フィットネス読者にも意味が通る
- 最後は「健康情報をどう判断するか」に戻る
- AI活用者がヘルスケアを発信している付加価値が自然に伝わる

## Postの基本仕様

- 1,500〜3,000字を基本にする
- 保存版記事は金曜21:00予約を基本にする
- 体験談またはAIツールあるあるから入り、最後に読者が使える判断基準へ落とす
- 効果断定ではなく、前提、個人差、判断材料を出す
- 最後はコメント/無料購読CTAにつなげる

## 推奨構成

```markdown
# タイトル

導入: 体験談またはAIツールあるある

## 先に結論
## なぜこのテーマが大事か
## 僕が迷ったこと/体験談
## AI好き目線で見ると
## よくある誤解
## 判断基準
## 例外・注意点
## まとめ
## コメント/購読CTA
```

## 安全ゲート

以下を含む場合は自動公開/自動予約しない。下書きだけ作成し、確認を求める。

- 疾患名
- 医薬品
- 妊娠/授乳
- 未成年
- 競技規則/ドーピング
- 「治る」「改善する」に近い健康主張
- 特定商品の強い購入推奨

下書き作成は品質スコア85点以上で可。

予約投稿は品質スコア90点以上で可。

メール配信あり予約は品質スコア92点以上、かつユーザーが「メールあり」と明示した場合だけ実行する。

## AIpreneurフック品質ゲート

下書き作成前に必ず本文を確認する。

- `## AI好き目線で見ると` セクション、または導入内のAIツールあるあるが入っていること
- AIあるあるが本文テーマの判断基準につながっていること
- 目的関数、RAG、ベクトルDBなど日常語から遠い専門語を比喩の中心にしていないこと
- AIの話だけで浮いておらず、クレアチン、プロテイン、食事、睡眠など本文テーマに戻っていること

この条件を満たさない場合、品質スコアは最大84点とし、`create_draft`、予約、公開を実行しない。本文を書き直してから再評価する。

## 実行フロー

1. `$ARGUMENTS` からテーマ、下書きのみ/予約/公開、予約日時、メール有無を読む。
2. テーマが空なら、`Substack 制作ボード.md` の次の保存版記事または `Substack 記事案.md` の最優先候補から選ぶ。
3. 既存原稿がある場合は `/Users/asyuyukiume/Brain Bulking/BrainBulking/02_SNS/Substack 投稿原稿/` から該当原稿を読む。
4. 既存原稿がなければ、上記構成でPost本文を作る。
5. 安全ゲートとAIpreneurフック品質ゲートを通す。
6. MCP/APIでSubstack下書きを作る。
7. ユーザーが予約を求めている場合、または保存版記事で日時が決まっている場合は予約する。
8. 作成/予約後、`Substack 公開ログ.md` と `Substack 制作ボード.md` を更新し、Obsidian vaultにも同期する。

## MCP/API実行メモ

下書き作成:

- `create_draft(title, content_markdown, subtitle?, audience="everyone")`

即時公開:

- `publish_draft(post_id, send_email, share_automatically=False)`
- 明示許可なしに即時公開しない

予約:

- `substack-mcp` の既存 `schedule_draft` は `/drafts/{id}/schedule` を叩くため、現在のSubstackでは404になることがある
- 実績のある現在の予約APIは以下
  - `GET https://brainbulking.substack.com/api/v1/drafts/{post_id}/prepublish?publish_date={ISO}`
  - `POST https://brainbulking.substack.com/api/v1/drafts/{post_id}/scheduled_release`
  - payload: `{"trigger_at": "...", "post_audience": "everyone"}`
  - メール配信ありの場合のみ `email_audience` を追加する

予約確認:

- `GET https://brainbulking.substack.com/api/v1/drafts/{post_id}`
- `postSchedules[].trigger_at` に予約時刻が入っていることを確認する

## 画像

Post画像は必須扱いにしない。画像を付ける場合は、ユーザー指定または明確な画像生成指示がある時だけ実行する。

## 出力

下書きのみ:

```markdown
下書きを作成しました。

- post_id:
- edit_url:
- 品質スコア:
- AIpreneurフック:
- 次アクション:
```

予約済み:

```markdown
予約しました。

- post_id:
- edit_url:
- 予約日時:
- send_email:
- AIpreneurフック:
- 予約確認:
```

公開済み:

```markdown
公開しました。

- post_id:
- public_url:
- send_email:
```
