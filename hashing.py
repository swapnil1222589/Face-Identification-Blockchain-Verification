from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_content_record(
    *,
    image_bytes: bytes,
    source_url: str,
    title: str = "",
    platform: str = "",
    snippet: str = "",
) -> bytes:
    """
    Build the exact deterministic record that gets hashed.

    The record contains:
      - SHA-256 of the discovered image bytes
      - source URL
      - title/platform/snippet metadata
    API keys and secrets are never included.
    """
    record: dict[str, Any] = {
        "image_sha256": hashlib.sha256(image_bytes).hexdigest(),
        "source_url": source_url.strip(),
        "title": title.strip(),
        "platform": platform.strip(),
        "snippet": snippet.strip(),
    }
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def content_fingerprint(
    *,
    image_bytes: bytes,
    source_url: str,
    title: str = "",
    platform: str = "",
    snippet: str = "",
) -> str:
    payload = canonical_content_record(
        image_bytes=image_bytes,
        source_url=source_url,
        title=title,
        platform=platform,
        snippet=snippet,
    )
    return hashlib.sha256(payload).hexdigest()
