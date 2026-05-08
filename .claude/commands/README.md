# Project Slash Commands

このディレクトリはClaude Codeのプロジェクト用スラッシュコマンド置き場。

## Substack

- `/substa-note テーマ`
  - `/substack-note` の短縮版
  - Substack内の短文 `Note` を作成する
  - 「投稿して」を含めると、品質ゲート後にMCP/API経由で投稿する

- `/substa-post テーマ`
  - `/substack-post` の短縮版
  - Substackの長文 `Post` を作成する
  - 「下書きだけ」「予約して」「2026-05-15 21:00」「メールあり」などを引数に含めて使う

- `/substack-note テーマ`
  - Substack内の短文 `Note` を作成する
  - 「投稿して」を含めると、品質ゲート後にMCP/API経由で投稿する

- `/substack-post テーマ`
  - Substackの長文 `Post` を作成する
  - 「下書きだけ」「予約して」「2026-05-15 21:00」「メールあり」などを引数に含めて使う

例:

```text
/substa-note プロテインを買う前に一回見ること 投稿して
/substa-post クレアチンはいつ飲むかより何gかを見る話 2026-05-15 21:00 予約して
/substack-note プロテインを買う前に一回見ること 投稿して
/substack-post クレアチンはいつ飲むかより何gかを見る話 2026-05-15 21:00 予約して
```
