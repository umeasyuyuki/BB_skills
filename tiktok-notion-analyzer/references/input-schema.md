# Input Schema

Provide one JSON object per post.

## Required metrics

- `views` (integer)
- `likes` (integer)
- `comments` (integer)
- `saves` (integer)

## Optional KPI metrics

- `swipe_completion_rate` (number, percent)
- `search_traffic_rate` (number, percent)
- `profile_visit_rate` (number, percent)
- `follow_conversion_rate` (number, percent)
- `profile_to_follow_rate` (number, percent)

## Recommended post fields

- `post_id` (string)
- `url` (string)
- `published_at` (ISO-8601 date or datetime string)
- `caption` (string)
- `content_summary` (string)
- `hook` (string, optional)
- `cta` (string, optional)
- `hashtags` (array of strings, optional)

## Supported shapes

Use either:

1. Nested form:
```json
{
  "post": {
    "post_id": "7420012345678900000",
    "url": "https://www.tiktok.com/@your_account/video/7420012345678900000",
    "published_at": "2026-02-01",
    "caption": "3 mistakes in morning routines",
    "content_summary": "Explains 3 mistakes and provides a corrected checklist",
    "hook": "Most people ruin focus before 9AM",
    "cta": "Save this and test tomorrow morning",
    "hashtags": ["#productivity", "#habits"]
  },
  "metrics": {
    "views": 125430,
    "likes": 6420,
    "comments": 388,
    "saves": 521,
    "swipe_completion_rate": 28.4,
    "search_traffic_rate": 16.0,
    "profile_visit_rate": 2.7,
    "follow_conversion_rate": 1.2
  }
}
```

2. Flat form:
```json
{
  "post_id": "7420012345678900000",
  "caption": "3 mistakes in morning routines",
  "content_summary": "Explains 3 mistakes and provides a corrected checklist",
  "views": 125430,
  "likes": 6420,
  "comments": 388,
  "saves": 521
}
```

## URL mode (no JSON file)

You can run directly from a TikTok URL:

```bash
python3 scripts/analyze_and_save.py --url "https://www.tiktok.com/@user/video/123" --allow-missing-metrics --dry-run
```

For full metric-based analysis, pass metrics on CLI:

```bash
python3 scripts/analyze_and_save.py --url "https://www.tiktok.com/@user/video/123" --views 10000 --likes 500 --comments 40 --saves 280 --dry-run
```
