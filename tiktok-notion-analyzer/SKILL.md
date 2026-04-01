---
name: tiktok-notion-analyzer
description: Analyze TikTok post content and performance metrics, explain why current engagement happened, and generate save-focused improvement actions with optional Notion database write-back. Use when reviewing TikTok posts by views/likes/comments/saves, preparing creator performance feedback, or storing structured analysis in Notion.
---

# TikTok Notion Analyzer

Analyze one TikTok post at a time with a repeatable framework, then store structured insights in Notion.
Use bundled scripts for deterministic output instead of rewriting ad hoc analysis each run.

## Workflow

1. Collect one post's input in JSON format.  
   Use the schema in `references/input-schema.md`.
   Load and apply `references/brand-strategy.md` before analysis.
2. Run the analyzer in dry-run mode first.  
   Command:
   ```bash
   python3 scripts/analyze_and_save.py --input references/sample-post-input.json --dry-run
   ```
   URL-only quick start (content-focused):
   ```bash
   python3 scripts/analyze_and_save.py --url "https://www.tiktok.com/@user/video/123" --allow-missing-metrics --dry-run
   ```
   URL + metrics (full analysis):
   ```bash
   python3 scripts/analyze_and_save.py --url "https://www.tiktok.com/@user/video/123" --views 10000 --likes 500 --comments 40 --saves 280 --dry-run
   ```
3. Review the generated:
   - engagement diagnosis (`why_engagement`)
   - save-focused actions (`save_improvements`)
   - derived rates (`save_rate`, `engagement_rate`, etc.)
4. Push to Notion after validation.  
   Set `NOTION_API_KEY` and one of `NOTION_DATA_SOURCE_ID` or `NOTION_DATABASE_ID`, then run:
   ```bash
   python3 scripts/analyze_and_save.py --input <your-post.json>
   ```
5. If Notion property names differ from defaults, pass a mapping file:
   ```bash
   python3 scripts/analyze_and_save.py --input <your-post.json> --property-map references/notion-property-map.json
   ```

## Input Contract

- Require metrics:
  - `views`
  - `likes`
  - `comments`
  - `saves`
  If metrics are unknown, run with `--allow-missing-metrics` for qualitative analysis only.
- Include content context:
  - `caption`
  - `content_summary`
  - optional `hook`, `cta`, `hashtags`, `url`, `published_at`

## Analysis Rules

1. Diagnose why engagement landed at the current level by combining:
   - rate benchmarks (`like_rate`, `comment_rate`, `save_rate`, `engagement_rate`)
   - content signal checks (structure clarity, specificity, CTA quality)
   - distribution signal checks (views vs quality-rate mismatch)
2. Prioritize improvements for save growth before other goals.
3. Give actionable recommendations with direct production implications:
   - script structure changes
   - shot/composition changes
   - CTA timing
   - packaging (cover/title/caption pattern)
4. Keep recommendations testable in the next post iteration.

## Notion Write Rules

1. Default to writing a new page in the configured database.
2. Keep the following canonical fields in sync:
   - `title`, `post_id`, `url`, `published_at`
   - `views`, `likes`, `comments`, `saves`
   - `engagement_rate`, `like_rate`, `comment_rate`, `save_rate`
   - `content_summary`, `why_engagement`, `save_improvements`, `analysis_markdown`
3. When schema mismatch occurs, provide a property map JSON instead of changing script internals.
4. Preserve dry-run as the first execution in each new workspace.

## Output Contract

Return a structured object that includes:
- normalized post and metrics
- derived rates
- concise summary
- `why_engagement` list
- `save_improvements` list
- `strategy_alignment` (pillar fit, KPI status, guardrail flags)
- optional Notion page URL or ID when written successfully

## Resource Map

- `scripts/analyze_and_save.py`: deterministic analysis and optional Notion write-back.
- `references/input-schema.md`: exact JSON schema and examples.
- `references/brand-strategy.md`: mission, pillar constraints, KPI targets, compliance guardrails.
- `references/notion-database-template.md`: recommended Notion database columns.
- `references/notion-property-map.json`: canonical-to-actual property-name mapping template.
- `references/sample-post-input.json`: sample input for dry-run testing.

## Validation

Run:
```bash
python3 /Users/asyuyukiume/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/asyuyukiume/.codex/skills/tiktok-notion-analyzer
```

Run a functional dry-run test:
```bash
python3 scripts/analyze_and_save.py --input references/sample-post-input.json --dry-run --output /tmp/tiktok-analysis.json
```
