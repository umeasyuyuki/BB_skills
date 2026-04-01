# Notion Database Template

Create a Notion database with the following default property names and types.
If your names differ, update `references/notion-property-map.json`.

| Property | Type | Canonical Key |
|---|---|---|
| Name | Title | `title` |
| Post ID | Rich text | `post_id` |
| Post URL | URL | `url` |
| Published At | Date | `published_at` |
| Views | Number | `views` |
| Likes | Number | `likes` |
| Comments | Number | `comments` |
| Saves | Number | `saves` |
| Engagement Rate | Number | `engagement_rate` |
| Like Rate | Number | `like_rate` |
| Comment Rate | Number | `comment_rate` |
| Save Rate | Number | `save_rate` |
| Content Summary | Rich text | `content_summary` |
| Why Engagement | Rich text | `why_engagement` |
| Save Improvements | Rich text | `save_improvements` |
| Analysis | Rich text | `analysis_markdown` |

## Environment Variables

Set both before non-dry runs:

```bash
export NOTION_API_KEY="secret_xxx"
export NOTION_DATABASE_ID="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

If you use Notion API version `2025-09-03+`, prefer:

```bash
export NOTION_API_KEY="secret_xxx"
export NOTION_DATA_SOURCE_ID="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

## Run Commands

Dry-run:
```bash
python3 scripts/analyze_and_save.py --input references/sample-post-input.json --dry-run
```

Write to Notion:
```bash
python3 scripts/analyze_and_save.py --input references/sample-post-input.json
```
