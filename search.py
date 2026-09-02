from __future__ import annotations

import io
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

import requests


@dataclass
class SearchCandidate:
    title: str
    url: str
    domain: str
    image_url: str | None = None
    snippet: str | None = None
    platform: str | None = None
    source_type: str = "google_lens"
    raw: dict[str, Any] | None = None
    downloaded_image: bytes | None = None
    face_similarity: float | None = None
    status: str = "UNMATCHED"

    def public_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("downloaded_image", None)
        data.pop("raw", None)
        return data


class SearchProviderError(RuntimeError):
    pass


def _secret(name: str) -> str | None:
    value = os.getenv(name)
    if value:
        return value
    try:
        from google.colab import userdata  # type: ignore
        return userdata.get(name)
    except Exception:
        return None


def get_serpapi_key() -> str:
    key = _secret("SERPAPI_KEY")
    if not key:
        raise SearchProviderError(
            "SERPAPI_KEY is missing. Add it to Colab Secrets or an environment variable."
        )
    return key


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def _platform(domain: str) -> str:
    d = domain.lower()
    if "instagram" in d:
        return "Instagram"
    if "facebook" in d:
        return "Facebook"
    if "x.com" in d or "twitter" in d:
        return "X/Twitter"
    if "linkedin" in d:
        return "LinkedIn"
    if "youtube" in d:
        return "YouTube"
    if "tiktok" in d:
        return "TikTok"
    return domain


def _extract_items(results: dict[str, Any]) -> Iterable[dict[str, Any]]:
    # Google Lens can expose exact matches and visual matches with slightly
    # different fields. Keep this adapter intentionally tolerant.
    for key in ("exact_matches", "visual_matches", "image_results"):
        items = results.get(key) or []
        if isinstance(items, list):
            yield from items


def _candidate_from_item(item: dict[str, Any]) -> SearchCandidate | None:
    url = item.get("link") or item.get("url")
    if not isinstance(url, str) or not url.startswith(("http://", "https://")):
        return None

    image_url = (
        item.get("thumbnail")
        or item.get("image")
        or item.get("original")
        or item.get("image_url")
    )
    if image_url and not isinstance(image_url, str):
        image_url = None

    domain = _domain(url)
    return SearchCandidate(
        title=str(item.get("title") or "Untitled result"),
        url=url,
        domain=domain,
        image_url=image_url,
        snippet=str(item.get("snippet") or "") or None,
        platform=_platform(domain),
        raw=item,
    )


def search_web_for_image(
    image_path: str | Path,
    *,
    api_key: str | None = None,
    max_candidates: int = 12,
    timeout: int = 45,
) -> tuple[list[SearchCandidate], dict[str, Any]]:
    """
    Perform a genuine Google Lens reverse-image search through SerpApi.

    The local image is uploaded to SerpApi's Image API first, then the returned
    temporary image_id is submitted to the Google Lens engine.
    """
    try:
        import serpapi
    except ImportError as exc:
        raise SearchProviderError("Install the 'google-search-results' package.") from exc

    api_key = api_key or get_serpapi_key()
    client = serpapi.Client(api_key=api_key)

    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(image_path)

    # SerpApi's image upload limit is 500 KB. Compress if necessary.
    payload_path = image_path
    temp_path = None
    if image_path.stat().st_size > 480_000:
        from PIL import Image
        image = Image.open(image_path).convert("RGB")
        temp_path = image_path.with_name("_serpapi_upload.jpg")
        quality = 88
        while quality >= 45:
            image.save(temp_path, "JPEG", quality=quality, optimize=True)
            if temp_path.stat().st_size <= 480_000:
                break
            quality -= 5
        payload_path = temp_path

    try:
        upload = client.upload_image(str(payload_path))
        if "error" in upload:
            raise SearchProviderError(str(upload["error"]))

        image_id = upload.get("image_id")
        if not image_id:
            raise SearchProviderError("SerpApi did not return an image_id.")

        results = client.search({
            "engine": "google_lens",
            "image_id": image_id,
            "type": "all",
            "hl": "en",
            "gl": "in",
            "no_cache": "true",
        })

        if isinstance(results, dict) and results.get("error"):
            raise SearchProviderError(str(results["error"]))

        candidates: list[SearchCandidate] = []
        seen: set[str] = set()
        for item in _extract_items(results):
            candidate = _candidate_from_item(item)
            if not candidate or candidate.url in seen:
                continue
            seen.add(candidate.url)
            candidates.append(candidate)
            if len(candidates) >= max_candidates:
                break

        return candidates, results
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink(missing_ok=True)


def download_candidate_image(
    image_url: str,
    *,
    timeout: int = 15,
    max_bytes: int = 8_000_000,
) -> bytes:
    if not image_url.startswith(("http://", "https://")):
        raise ValueError("Candidate image URL must use HTTP(S).")

    headers = {
        "User-Agent": "FaceChainVerify/1.0 (hackathon prototype)",
        "Accept": "image/avif,image/webp,image/jpeg,image/png,*/*;q=0.8",
    }
    with requests.get(image_url, headers=headers, timeout=timeout, stream=True) as response:
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").lower()
        if content_type and not content_type.startswith("image/"):
            raise ValueError(f"URL did not return an image: {content_type}")

        chunks: list[bytes] = []
        total = 0
        for chunk in response.iter_content(chunk_size=64 * 1024):
            if not chunk:
                continue
            total += len(chunk)
            if total > max_bytes:
                raise ValueError("Candidate image exceeds the configured download limit.")
            chunks.append(chunk)
        data = b"".join(chunks)

    if not data:
        raise ValueError("Downloaded image is empty.")
    return data
