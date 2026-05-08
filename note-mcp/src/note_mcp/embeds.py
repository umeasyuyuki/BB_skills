"""Embed handling for YouTube / Twitter / note article URLs.

When a user types ``＋ → 埋め込み → URL → 適用`` in the note editor, two API
calls happen and a very specific ``<figure>`` shape gets saved to the body.
This module reproduces that flow from a Markdown source.

The shape note's editor saves (reverse-engineered from a captured draft_save
body, 2026-05):

    <figure name="<UUID>" id="<UUID>"
            data-src="<external URL>"
            data-identifier="null"
            embedded-service="youtube"
            embedded-content-key="<KEY FROM API>">
      <span><div style="…padding-bottom: 56.25%;…">
        <iframe src="https://www.youtube.com/embed/<VID>?rel=0" …></iframe>
      </div></span>
    </figure>

The inner ``<span><div>…iframe…</div></span>`` block is **not** something we
construct ourselves — it is the ``html_for_embed`` field returned by the API.
That is what makes the embed actually render (without it note's renderer
strips the figure to an empty shell).

Flow:
1. Convert standalone URL paragraphs in the markdown→html output into a
   *placeholder* ``<figure>`` carrying just the URL + service. The placeholder
   is opaque to note (no real key, no html_for_embed) and is only there so
   ``resolve_embed_keys`` can find and rewrite it after the draft exists.
2. After the draft is created (so we have an article_key), call
   ``GET /v2/embed_by_external_api`` for each placeholder to obtain
   ``{key, html_for_embed}`` and replace the placeholder with the final
   ``<figure>`` in the editor's exact shape.

The two-step flow is required because the embed API needs ``embeddable_key``
(= the parent article's key), which doesn't exist until the empty draft has
been created.
"""

from __future__ import annotations

import re
import uuid


# Service detection — order matters (most specific first)
_YOUTUBE = re.compile(
    r"^https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([\w-]+)",
    re.IGNORECASE,
)
_TWITTER = re.compile(
    r"^https?://(?:www\.)?(?:twitter\.com|x\.com)/\w+/status/(\d+)",
    re.IGNORECASE,
)
_NOTE_ARTICLE = re.compile(
    r"^https?://note\.com/[\w-]+/n/(n[a-z0-9]+)",
    re.IGNORECASE,
)


def detect_embed_service(url: str) -> str | None:
    if _YOUTUBE.match(url):
        return "youtube"
    if _TWITTER.match(url):
        return "twitter"
    if _NOTE_ARTICLE.match(url):
        return "note"
    return None


# After markdown→HTML, paragraphs containing only a URL look like:
#   <p>https://youtube.com/watch?v=xxx</p>
# (UUIDs may have been added already; handle both shapes)
_URL_PARAGRAPH = re.compile(
    r'<p(?:\s+name="[^"]+"\s+id="[^"]+")?>\s*(https?://\S+?)\s*</p>',
    re.IGNORECASE,
)

# Trailing punctuation that is almost never part of a real URL. Stripped before
# detection so a sentence like "見てください。" won't end up baked into the embed key
# lookup. (The skill tells the agent not to write punctuation after URLs, but be
# defensive — natural Japanese writing makes this slip through.)
_URL_TRAILING_PUNCT = ".,;:!?。、）)]}>"

# Marker attribute that distinguishes a placeholder figure (waiting for embed
# key resolution) from a fully-resolved one. Removed in resolve_embed_keys.
_PLACEHOLDER_MARKER = 'data-embed-pending="1"'


def _build_placeholder_figure(url: str, service: str) -> str:
    """Build a placeholder <figure> that resolve_embed_keys will swap out.

    The shape here doesn't matter for note's renderer (this never reaches the
    server in the final body); it just needs enough info — the URL and the
    service — for ``resolve_embed_keys`` to find the placeholder and call the
    embed API with the right params.
    """
    fig_uid = str(uuid.uuid4())
    return (
        f'<figure name="{fig_uid}" id="{fig_uid}" '
        f'embedded-service="{service}" data-src="{url}" '
        f"{_PLACEHOLDER_MARKER}></figure>"
    )


def inject_embed_placeholders(html: str) -> str:
    """Replace <p>URL</p> blocks with <figure> placeholders for known services."""

    def _repl(match: re.Match[str]) -> str:
        url = match.group(1).strip().rstrip(_URL_TRAILING_PUNCT)
        service = detect_embed_service(url)
        if not service:
            return match.group(0)
        return _build_placeholder_figure(url, service)

    return _URL_PARAGRAPH.sub(_repl, html)


# Match a placeholder figure and capture its UUID, service, and URL.
_PLACEHOLDER_FIGURE = re.compile(
    r'<figure\s+name="(?P<name>[^"]+)"\s+id="(?P<id>[^"]+)"\s+'
    r'embedded-service="(?P<service>[^"]+)"\s+data-src="(?P<url>[^"]+)"\s+'
    + re.escape(_PLACEHOLDER_MARKER)
    + r'></figure>',
    re.IGNORECASE,
)


def find_embed_placeholders(html: str) -> list[dict[str, str]]:
    """Return placeholder figures that still need embed-key resolution."""
    out: list[dict[str, str]] = []
    for m in _PLACEHOLDER_FIGURE.finditer(html):
        out.append(
            {
                "url": m.group("url"),
                "service": m.group("service"),
                "name": m.group("name"),
                "id": m.group("id"),
            }
        )
    return out


def _build_resolved_figure(
    *,
    name: str,
    id_: str,
    url: str,
    service: str,
    content_key: str,
    html_for_embed: str,
) -> str:
    """Build the final <figure> in the exact shape note's editor saves.

    ``html_for_embed`` is provided by ``/v2/embed_by_external_api`` and is the
    pre-rendered iframe wrapper; do not modify it.
    """
    return (
        f'<figure name="{name}" id="{id_}" '
        f'data-src="{url}" data-identifier="null" '
        f'embedded-service="{service}" '
        f'embedded-content-key="{content_key}">'
        f"{html_for_embed}"
        f"</figure>"
    )


async def resolve_embed_keys(html: str, article_key: str) -> str:
    """Resolve placeholder figures against ``/v2/embed_by_external_api``.

    For each placeholder produced by ``inject_embed_placeholders``:

        GET /api/v2/embed_by_external_api
            ?url=<external URL>
            &service=youtube|twitter|note
            &embeddable_key=<article_key>     ← parent note this embed belongs to
            &embeddable_type=Note             ← literal string

        → { data: { key: "<embed key>", html_for_embed: "<span>…iframe…</span>" } }

    Then replaces the placeholder with the editor's actual figure shape using
    the returned ``key`` and ``html_for_embed``.

    Returns the original HTML on best-effort failure (the empty placeholder
    stays in the body, which renders as a blank space — better than crashing
    the whole save).
    """
    placeholders = find_embed_placeholders(html)
    if not placeholders:
        return html

    # Late import to avoid circular dependency (client → markdown → embeds → client)
    from note_mcp.client import NoteClient

    async with NoteClient() as client:
        for ph in placeholders:
            try:
                response = await client.get(
                    "/v2/embed_by_external_api",
                    params={
                        "url": ph["url"],
                        "service": ph["service"],
                        "embeddable_key": article_key,
                        "embeddable_type": "Note",
                    },
                )
                data = response.get("data", {})
                server_key = data.get("key") or data.get("embed_key")
                html_for_embed = data.get("html_for_embed") or data.get("htmlForEmbed") or ""
                if not server_key or not html_for_embed:
                    continue
                resolved = _build_resolved_figure(
                    name=ph["name"],
                    id_=ph["id"],
                    url=ph["url"],
                    service=ph["service"],
                    content_key=str(server_key),
                    html_for_embed=str(html_for_embed),
                )
                # Replace this specific placeholder by its UUID (uniquely
                # identifies one figure even if the same URL appears twice).
                target = re.compile(
                    r'<figure\s+name="' + re.escape(ph["name"]) + r'"[^>]*?'
                    + re.escape(_PLACEHOLDER_MARKER) + r'></figure>',
                    re.IGNORECASE,
                )
                html = target.sub(lambda _m: resolved, html, count=1)
            except Exception:
                # Embed resolution is best-effort — leave the placeholder if it
                # fails. The empty <figure> renders as blank space on note,
                # which is recoverable (re-run update_article) without losing
                # the rest of the body.
                continue
    return html
