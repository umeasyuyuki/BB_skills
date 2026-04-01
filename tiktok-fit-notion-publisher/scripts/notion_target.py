#!/usr/bin/env python3
"""Manage project-local Notion target configuration."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DEFAULT_CONFIG = SKILL_DIR / ".notion-target.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Set/show local Notion target config")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="Config file path")
    parser.add_argument("--show", action="store_true", help="Show current resolved target")
    parser.add_argument("--clear", action="store_true", help="Delete local config file")
    parser.add_argument("--data-source-id", default="", help="Set notion_data_source_id")
    parser.add_argument("--database-id", default="", help="Set notion_database_id")
    parser.add_argument("--api-key", default="", help="Set notion_api_key (optional)")
    return parser.parse_args()


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def save_config(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def resolved(config: dict[str, Any]) -> dict[str, Any]:
    ds = config.get("notion_data_source_id") or os.getenv("NOTION_DATA_SOURCE_ID", "")
    db = config.get("notion_database_id") or os.getenv("NOTION_DATABASE_ID", "")
    token = config.get("notion_api_key") or os.getenv("NOTION_API_KEY", "")
    return {
        "notion_data_source_id": ds,
        "notion_database_id": db,
        "notion_api_key_set": bool(token),
    }


def main() -> int:
    args = parse_args()
    cfg_path = args.config

    if args.clear:
        if cfg_path.exists():
            cfg_path.unlink()
        print(json.dumps({
            "ok": True,
            "action": "cleared",
            "config": str(cfg_path),
            "resolved": resolved({}),
        }, ensure_ascii=False, indent=2))
        return 0

    cfg = load_config(cfg_path)
    updated = False

    if args.data_source_id.strip():
        cfg["notion_data_source_id"] = args.data_source_id.strip()
        updated = True
    if args.database_id.strip():
        cfg["notion_database_id"] = args.database_id.strip()
        updated = True
    if args.api_key.strip():
        cfg["notion_api_key"] = args.api_key.strip()
        updated = True

    if updated:
        save_config(cfg_path, cfg)
        action = "updated"
    elif args.show:
        action = "show"
    else:
        action = "noop"

    print(json.dumps({
        "ok": True,
        "action": action,
        "config": str(cfg_path),
        "config_exists": cfg_path.exists(),
        "config_values": {
            "notion_data_source_id": cfg.get("notion_data_source_id", ""),
            "notion_database_id": cfg.get("notion_database_id", ""),
            "notion_api_key_set": bool(cfg.get("notion_api_key", "")),
        },
        "resolved": resolved(cfg),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
