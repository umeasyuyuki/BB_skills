# note.com 下書き保存ルール

Phase 4 の Notion 保存後、確定した Note 記事を note.com の下書きへ保存する。保存には `note-mcp` を使う。公開はユーザーの明示許可があるまで行わない。

## 前提

- `note-mcp` が MCP クライアントに登録済み
- `note_check_auth` が `authenticated: true` を返す
- 未ログインの場合は `note_import_chrome_cookies(browser="chrome", profile="Profile 4", verify=true)` で `brain_bulking` の Cookie を取り込む
- `note_import_chrome_cookies` でも失敗した場合だけ、Chrome 側の note.com 再ログインを案内して中断する
- 対象は自分の note アカウントのみ

## 使用ツール

| ツール | 用途 |
|---|---|
| `note_import_chrome_cookies` | 普段の Chrome / Brave / Chromium から note.com Cookie を取り込む |
| `note_check_auth` | note.com 認証状態の確認 |
| `note_create_draft` | Markdown 本文から下書き作成 |
| `note_get_preview_url` | 下書きのプレビュー URL 発行 |
| `note_update_article` | 下書き修正時の更新 |
| `note_publish_article` | 公開。明示許可がある時だけ使用 |

## 下書き保存フロー

1. Phase 3 の薬機法チェックが Green、または Yellow をユーザーが許容したことを確認する
2. Phase 4 の Notion 保存を完了し、制作ログを残す
3. Note 記事本文から保存用 Markdown を作る
4. `note_check_auth` を実行する
5. 未認証なら `note_import_chrome_cookies(browser="chrome", profile="Profile 4", verify=true)` を実行し、再度認証状態を確認する
6. 認証済みなら `note_create_draft(title, body_markdown, tags)` を実行する
7. 成功したら `note_get_preview_url(article_key)` を実行する
8. `article_key`、preview URL、Notion Note URL をユーザーに返す
9. Threads 最終リプの `【★Note URL を貼る★】` は、公開 URL が確定するまで置換しない

## 目次

note.com の目次は H2/H3 見出しから自動生成される。目次位置を固定したい場合は、本文の導入直後に `[TOC]` を単独行で入れる。

標準構成:

```markdown
# {タイトル}

{導入}

[TOC]

## {見出し1}
...
```

ルール:

- `[TOC]` は単独行にする
- 前後に空行を入れる
- `##` と `###` 以外の見出しは使わない
- note.com で目次位置が崩れる場合は `[TOC]` を外し、note 側の自動目次に任せる

## note.com 投入用 Markdown

Notion 保存用の管理メタ情報は note.com には入れない。

除外するもの:

- `title_input:`
- `文字数:`
- `カテゴリ:`
- `セクション数:`
- `脚注数:`
- `関連リンク案内:`
- `専門用語翻訳チェック:`
- `セルフチェック結果:`
- `---` 以下のセルフチェックブロック

残すもの:

- タイトル
- 導入
- `[TOC]`
- 本文 H2/H3
- 関連リンク
- 脚注

## タグ

`note_create_draft` の `tags` は原則以下から 3〜5 個にする。`#` は付けない。

- BrainBulking
- 筋トレ
- 栄養
- サプリ
- 健康情報
- プロテイン
- クレアチン

テーマに合わないタグは入れない。

## 公開ガードレール

- `note_publish_article` はユーザーが「公開して」と明示した時だけ呼ぶ
- 下書き作成は自動でよい
- 有料設定、マガジン、メンバーシップ、アイキャッチは別タスクとして扱う
- 自動運用時も、薬機法 Red は絶対に下書き保存しない

## エラー処理

| エラー | 対処 |
|---|---|
| note-mcp ツールが見えない | MCP 未登録として中断し、セットアップを案内 |
| `note_check_auth` が false | `note_import_chrome_cookies` を実行し、Chrome Cookie 取り込みを試す |
| `note_import_chrome_cookies` が失敗 | 普段の Chrome で note.com にログイン済みか確認。macOS Keychain 許可が必要な場合は許可する |
| `note_create_draft` 失敗 | 1 回だけ再試行。失敗時は Notion URL とローカルバックアップ先を返す |
| preview URL 発行失敗 | article key は返し、note.com 管理画面で確認するよう案内 |

## 完全自動化への移行条件

以下を満たすまでは、下書き保存までに留める。

- 直近 5 本で薬機法 Red なし
- Claude/Codex 生成文の手戻りが軽微
- 目次、脚注、関連リンクが note.com プレビューで崩れていない
- タイトルと本文に誇大表現がない
- ユーザーが公開前チェック不要と明示している

完全自動化後も `note_publish_article` は段階的に解禁する。最初は「下書き自動保存」まで、次に「ユーザー確認後に公開」、最後に「Green 判定のみ自動公開」の順に進める。
