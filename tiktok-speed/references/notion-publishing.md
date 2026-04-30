# Notion Publishing

## Goal

高速版の成果物をNotionへ保存する。画像ファイルやDriveリンクではなく、ChatGPT画像生成Projectに貼るプロンプトを保存する。

## Package

`tiktok-fit-notion-publisher` を使う場合は、以下の構造にする。

```json
{
  "title": "{採用タイトル}",
  "theme": "{入力テーマ}",
  "workflow": "tiktok-speed",
  "content_type": "carousel",
  "status": "承認済み",
  "approved": true,
  "tags": ["tiktok-speed", "{category}"],
  "sections": {
    "title_suggestions": "タイトル案Markdown",
    "script": "台本Markdown",
    "image_generation_prompts": "画像生成プロンプトMarkdown",
    "summary_table": "まとめ表Markdown",
    "caption": "キャプションMarkdown",
    "references": "根拠リンクMarkdown",
    "compliance_check": "薬機法・表現チェックMarkdown"
  }
}
```

## Required Sections

| section | 内容 |
|---|---|
| `title_suggestions` | 採用タイトル、候補、採用理由 |
| `script` | 6〜7枚の台本 |
| `image_generation_prompts` | ChatGPT画像生成Projectに貼るコピペ用プロンプト |
| `summary_table` | Notion用まとめ表 |
| `caption` | TikTok投稿キャプション |
| `references` | 根拠リンク。確認済みURLのみ |
| `compliance_check` | 薬機法・表現リスクの簡易チェック |

## Notes

- `content_type` は既存DB互換のため `carousel` を使う。
- `workflow` で `tiktok-speed` を入れ、通常の `contents-fullmake` と区別する。
- 画像生成プロンプトは必ずNotion本文に保存する。
- `image_links` は使わない。
- Driveアップロード結果は保存しない。
- キャプションは3500字必須にしない。
