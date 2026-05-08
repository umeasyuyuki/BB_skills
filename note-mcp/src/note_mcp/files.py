"""Audio + arbitrary-file upload.

Endpoints reverse-engineered from the editor JS bundle (2026-05):

- ``POST /v3/sounds/presigned_posts`` — body ``{filename, size}`` → presigned S3 POST
- ``POST <s3_action>``               — upload bytes to S3
- ``POST /v3/sounds``                — multipart {note_key, upload_key, filename,
                                       title, [description], [artist_name],
                                       [downloadable], [image_file]} → sound resource
                                       with ``html_for_embed`` + ``key``
- ``POST /v2/attachments/upload``    — single-shot file upload (multipart {file,
                                       file_name, note_key}) → attachment with
                                       ``html_for_embed`` + content key

The server returns ``html_for_embed`` (a pre-rendered fragment); we wrap it in
the editor's ``<figure embedded-service="...">`` shape and append it to the
draft body. This mirrors the embed flow in ``embeds.py``.

Field-name defense: note's API mixes snake_case (older endpoints) and
camelCase (newer); we read both. Same idea as ``embeds.resolve_embed_keys``.
"""

from __future__ import annotations

import html as html_module
import uuid
from pathlib import Path
from typing import Any

from note_mcp.client import NoteAPIError, NoteClient

# Constraints from the editor JS:
#   sounds: ≤100MB, .mp3/.aac/.m4a only
AUDIO_MAX_SIZE = 100 * 1024 * 1024
AUDIO_EXTS = {".mp3", ".aac", ".m4a"}
AUDIO_CONTENT_TYPES = {
    ".mp3": "audio/mpeg",
    ".aac": "audio/aac",
    ".m4a": "audio/mp4",
}

# Attachments: the editor doesn't enforce a strict allowlist (the server does).
# Use a generous cap; reject only the obvious oversize before the round-trip.
FILE_MAX_SIZE = 50 * 1024 * 1024


def _validate_audio(path: Path) -> None:
    if not path.exists():
        raise NoteAPIError(0, "audio file not found", str(path))
    ext = path.suffix.lower()
    if ext not in AUDIO_EXTS:
        raise NoteAPIError(
            0,
            f"unsupported audio extension {ext} (allowed: {sorted(AUDIO_EXTS)})",
            str(path),
        )
    size = path.stat().st_size
    if size > AUDIO_MAX_SIZE:
        raise NoteAPIError(
            0,
            f"audio too large ({size} bytes, max {AUDIO_MAX_SIZE})",
            str(path),
        )
    if size <= 0:
        raise NoteAPIError(0, "audio file is empty", str(path))


def _validate_file(path: Path) -> None:
    if not path.exists():
        raise NoteAPIError(0, "file not found", str(path))
    size = path.stat().st_size
    if size > FILE_MAX_SIZE:
        raise NoteAPIError(0, f"file too large ({size} bytes, max {FILE_MAX_SIZE})", str(path))
    if size <= 0:
        raise NoteAPIError(0, "file is empty", str(path))


def _pick(d: dict[str, Any], *keys: str) -> Any:
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return None


async def upload_audio(
    file_path: str,
    article_key: str,
    *,
    title: str | None = None,
    description: str | None = None,
    artist_name: str | None = None,
    downloadable: bool | None = None,
) -> dict[str, Any]:
    """Upload audio (.mp3/.aac/.m4a) and return note-sound embed metadata.

    The flow mirrors what the editor does when you click "音声":

      1. presigned_posts  → S3 destination
      2. POST file to S3
      3. POST /v3/sounds with the upload_key + metadata → embed resource

    Returns a dict with ``embedded_content_key``, ``html_for_embed``,
    ``identifier``, ``src`` — enough to splice into the article body.
    """
    if article_key.isdigit() or not article_key.startswith("n"):
        raise NoteAPIError(0, "upload_audio requires article key (n…)", article_key)

    path = Path(file_path)
    _validate_audio(path)
    ext = path.suffix.lower()
    content_type = AUDIO_CONTENT_TYPES[ext]
    file_bytes = path.read_bytes()
    audio_title = title or path.stem

    async with NoteClient() as client:
        # Step 1: presigned post
        presign = await client.post(
            "/v3/sounds/presigned_posts",
            json={"filename": path.name, "size": len(file_bytes)},
        )
        d = presign.get("data", {}) or {}
        action = _pick(d, "action", "url")
        post_fields = _pick(d, "post", "fields") or {}
        upload_key = _pick(d, "upload_key", "uploadKey", "key")
        if not action or not post_fields or not upload_key:
            raise NoteAPIError(
                0,
                "/v3/sounds/presigned_posts missing action/post/upload_key",
                str(presign)[:300],
            )

        # Step 2: S3 upload
        s3_response = await client.post_absolute(
            action,
            data=post_fields,
            files={"file": (path.name, file_bytes, content_type)},
        )
        if not s3_response.is_success:
            raise NoteAPIError(
                s3_response.status_code,
                "S3 upload failed",
                s3_response.text[:300],
            )

        # Step 3: create sound resource → returns embed
        form_data: dict[str, Any] = {
            "note_key": article_key,
            "upload_key": str(upload_key),
            "filename": path.name,
            "title": audio_title,
        }
        if description:
            form_data["description"] = description
        if artist_name:
            form_data["artist_name"] = artist_name
        if downloadable is not None:
            form_data["downloadable"] = "true" if downloadable else "false"

        # /v3/sounds expects multipart even without files; pass empty files dict
        sound_response = await client.post(
            "/v3/sounds",
            data=form_data,
            files={"_": ("", "", "")},  # force multipart encoding
        )

    sound = sound_response.get("data", {}) or {}
    html_for_embed = _pick(sound, "html_for_embed", "htmlForEmbed") or ""
    embed_key = _pick(sound, "key", "embedded_content_key", "embeddedContentKey")
    identifier = _pick(sound, "identifier", "id")
    src = _pick(sound, "url", "src", "play_url", "playUrl")

    if not html_for_embed or not embed_key:
        raise NoteAPIError(
            0,
            "POST /v3/sounds returned no html_for_embed or key",
            str(sound_response)[:300],
        )

    return {
        "embedded_content_key": str(embed_key),
        "html_for_embed": str(html_for_embed),
        "identifier": str(identifier) if identifier else None,
        "src": str(src) if src else None,
        "service": "note-sound",
        "size_bytes": len(file_bytes),
        "title": audio_title,
    }


async def upload_file(
    file_path: str,
    article_key: str,
    *,
    file_name: str | None = None,
) -> dict[str, Any]:
    """Upload an arbitrary file as a note attachment. Single-shot endpoint.

    Returns the embed metadata needed to splice an ``<figure
    embedded-service="attachment">`` block into the article body.
    """
    if article_key.isdigit() or not article_key.startswith("n"):
        raise NoteAPIError(0, "upload_file requires article key (n…)", article_key)

    path = Path(file_path)
    _validate_file(path)
    file_bytes = path.read_bytes()
    name = file_name or path.name

    async with NoteClient() as client:
        response = await client.post(
            "/v2/attachments/upload",
            data={"file_name": name, "note_key": article_key},
            files={"file": (name, file_bytes, "application/octet-stream")},
        )

    data = response.get("data", {}) or {}
    if isinstance(data, dict) and "error" in data:
        raise NoteAPIError(0, "attachments/upload returned error", str(data)[:300])

    html_for_embed = _pick(data, "html_for_embed", "htmlForEmbed") or ""
    embed_key = _pick(data, "embedded_content_key", "embeddedContentKey", "key")

    if not html_for_embed or not embed_key:
        raise NoteAPIError(
            0,
            "POST /v2/attachments/upload returned no html_for_embed or key",
            str(response)[:300],
        )

    return {
        "embedded_content_key": str(embed_key),
        "html_for_embed": str(html_for_embed),
        "service": "attachment",
        "size_bytes": len(file_bytes),
        "filename": name,
    }


def build_audio_figure(
    *,
    embedded_content_key: str,
    html_for_embed: str,
    identifier: str | None,
    src: str | None,
) -> str:
    """Build the ``<figure embedded-service="note-sound">`` shape note saves."""
    fig_uid = str(uuid.uuid4())
    src_attr = html_module.escape(src) if src else ""
    ident_attr = html_module.escape(identifier) if identifier else "null"
    return (
        f'<figure name="{fig_uid}" id="{fig_uid}" '
        f'data-src="{src_attr}" data-identifier="{ident_attr}" '
        f'embedded-service="note-sound" '
        f'embedded-content-key="{html_module.escape(embedded_content_key)}">'
        f"{html_for_embed}"
        f"</figure>"
    )


def build_file_figure(
    *,
    embedded_content_key: str,
    html_for_embed: str,
) -> str:
    """Build the ``<figure embedded-service="attachment">`` shape."""
    fig_uid = str(uuid.uuid4())
    return (
        f'<figure name="{fig_uid}" id="{fig_uid}" '
        f'embedded-service="attachment" '
        f'embedded-content-key="{html_module.escape(embedded_content_key)}">'
        f"{html_for_embed}"
        f"</figure>"
    )


def build_toc_block() -> str:
    """Build the ``<table-of-contents>`` block.

    note's editor schema parses ``<table-of-contents name="UUID" id="UUID">``
    as the TOC node and renders the live h2/h3 outline in its place. The
    element is empty — the renderer fills it.
    """
    uid = str(uuid.uuid4())
    return f'<table-of-contents name="{uid}" id="{uid}"></table-of-contents>'
