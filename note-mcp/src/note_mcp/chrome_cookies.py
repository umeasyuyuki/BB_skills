"""Import note.com cookies from the user's existing Chrome profile.

This mirrors the Substack MCP auth strategy: use the browser session the user
already trusts, then store only note.com cookies in note-mcp's own session file.
The Chrome profile is copied to a temporary directory before SQLite reads so we
do not attach Playwright to, or mutate, the user's live browser profile.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from note_mcp import session as session_store

NOTE_URL = "https://note.com"
REQUIRED_COOKIE = "_note_session_v5"

SUPPORTED_BROWSERS = ("chrome", "brave", "chromium")


class ChromeCookieImportError(RuntimeError):
    pass


@dataclass(frozen=True)
class CookieSource:
    browser: str
    profile: str
    cookie_file: Path


def _browser_type(browser: str) -> Any:
    try:
        from pycookiecheat import BrowserType
    except ImportError as exc:
        raise ChromeCookieImportError(
            "pycookiecheat is not installed. Install note-mcp dependencies again."
        ) from exc

    try:
        return {
            "chrome": BrowserType.CHROME,
            "brave": BrowserType.BRAVE,
            "chromium": BrowserType.CHROMIUM,
        }[browser]
    except KeyError as exc:
        raise ChromeCookieImportError(
            f"Unsupported browser={browser!r}. Supported: {', '.join(SUPPORTED_BROWSERS)}"
        ) from exc


def _browser_root(browser: str) -> Path:
    if sys.platform != "darwin":
        raise ChromeCookieImportError("Chrome cookie import currently supports macOS only.")

    app_support = Path.home() / "Library" / "Application Support"
    roots = {
        "chrome": app_support / "Google" / "Chrome",
        "brave": app_support / "BraveSoftware" / "Brave-Browser",
        "chromium": app_support / "Chromium",
    }
    try:
        return roots[browser]
    except KeyError as exc:
        raise ChromeCookieImportError(
            f"Unsupported browser={browser!r}. Supported: {', '.join(SUPPORTED_BROWSERS)}"
        ) from exc


def _discover_cookie_sources(browser: str, profile: str | None) -> list[CookieSource]:
    root = _browser_root(browser)
    if not root.exists():
        raise ChromeCookieImportError(f"{browser} profile root was not found: {root}")

    profile_names = [profile] if profile else ["Default"]
    if profile is None:
        profile_names.extend(
            sorted(
                child.name
                for child in root.iterdir()
                if child.is_dir() and child.name.startswith("Profile ")
            )
        )

    sources: list[CookieSource] = []
    for name in profile_names:
        cookie_file = root / name / "Cookies"
        if cookie_file.exists():
            sources.append(CookieSource(browser=browser, profile=name, cookie_file=cookie_file))

    if not sources:
        target = f"{browser}/{profile}" if profile else browser
        raise ChromeCookieImportError(f"No Chrome cookie database found for {target}.")
    return sources


def _copy_cookie_db(source: Path, temp_dir: Path) -> Path:
    copied = temp_dir / "Cookies"
    shutil.copy2(source, copied)
    for suffix in ("-wal", "-shm"):
        sidecar = source.with_name(source.name + suffix)
        if sidecar.exists():
            shutil.copy2(sidecar, copied.with_name(copied.name + suffix))
    return copied


def _read_note_cookies(source: CookieSource) -> dict[str, str]:
    try:
        from pycookiecheat import chrome_cookies
    except ImportError as exc:
        raise ChromeCookieImportError(
            "pycookiecheat is not installed. Install note-mcp dependencies again."
        ) from exc

    browser_type = _browser_type(source.browser)
    with tempfile.TemporaryDirectory(prefix="note-mcp-cookies-") as tmp:
        copied_cookie_file = _copy_cookie_db(source.cookie_file, Path(tmp))
        try:
            cookies = chrome_cookies(
                NOTE_URL,
                browser=browser_type,
                cookie_file=copied_cookie_file,
            )
        except Exception as exc:
            message = str(exc)
            if any(token in message.lower() for token in ("keychain", "safe storage", "password")):
                raise ChromeCookieImportError(
                    "Could not decrypt Chrome cookies. Allow macOS Keychain access for Chrome Safe Storage."
                ) from exc
            raise ChromeCookieImportError(
                f"Could not read cookies from {source.browser}/{source.profile}: {message}"
            ) from exc

    return {str(k): str(v) for k, v in cookies.items() if v is not None}


def _save_imported_cookies(cookies: dict[str, str], source: CookieSource) -> dict[str, Any]:
    if not cookies.get(REQUIRED_COOKIE):
        raise ChromeCookieImportError(
            f"{source.browser}/{source.profile} has no {REQUIRED_COOKIE} cookie for note.com."
        )

    saved = session_store.load_session() or {}
    merged_cookies = saved.get("cookies") or {}
    merged_cookies.update(cookies)
    saved.update(
        {
            "cookies": merged_cookies,
            "auth_source": {
                "type": "chrome_cookie_import",
                "browser": source.browser,
                "profile": source.profile,
            },
        }
    )
    session_store.save_session(saved)
    return saved


def import_note_cookies_from_chrome(
    *,
    browser: str = "chrome",
    profile: str | None = None,
) -> dict[str, Any]:
    """Import note.com cookies from a Chrome-family browser profile.

    Args:
        browser: chrome, brave, or chromium.
        profile: Chrome profile name such as "Default" or "Profile 4".
            When omitted, Default and Profile N directories are tried in order.

    Returns:
        Metadata only. Cookie values are never returned.
    """
    browser = browser.lower().strip()
    last_error: Exception | None = None
    for source in _discover_cookie_sources(browser, profile):
        try:
            cookies = _read_note_cookies(source)
            _save_imported_cookies(cookies, source)
            return {
                "imported": True,
                "browser": source.browser,
                "profile": source.profile,
                "cookie_count": len(cookies),
                "cookie_names": sorted(cookies.keys()),
                "required_cookie": REQUIRED_COOKIE,
            }
        except ChromeCookieImportError as exc:
            last_error = exc
            if profile:
                raise
            continue

    raise ChromeCookieImportError(str(last_error) if last_error else "No usable note.com cookies found.")
