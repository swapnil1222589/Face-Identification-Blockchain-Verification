from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse


def validate_http_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False


def mask_secret(value: str | None) -> str:
    if not value:
        return "<missing>"
    if len(value) <= 8:
        return "***"
    return value[:4] + "…" + value[-4:]


def env_or_colab_secret(name: str) -> str | None:
    value = os.getenv(name)
    if value:
        return value
    try:
        from google.colab import userdata  # type: ignore
        return userdata.get(name)
    except Exception:
        return None
