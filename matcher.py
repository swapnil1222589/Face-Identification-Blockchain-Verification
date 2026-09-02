from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Iterable

import cv2
import numpy as np

from .face import FaceEngine, FaceResult, cosine_similarity
from .search import SearchCandidate, download_candidate_image


@dataclass
class MatchConfig:
    threshold: float = 0.55
    max_faces_per_candidate: int = 8


def _decode_image(data: bytes) -> np.ndarray:
    array = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Downloaded content is not a decodable image.")
    return image


def best_face_similarity(
    engine: FaceEngine,
    target_embedding: np.ndarray,
    image_bytes: bytes,
    *,
    max_faces: int = 8,
) -> float | None:
    image = _decode_image(image_bytes)
    faces = engine.detect(image)[:max_faces]
    if not faces:
        return None
    return max(cosine_similarity(target_embedding, f.embedding) for f in faces)


def rank_candidates(
    engine: FaceEngine,
    target_embedding: np.ndarray,
    candidates: Iterable[SearchCandidate],
    *,
    config: MatchConfig | None = None,
) -> list[SearchCandidate]:
    config = config or MatchConfig()
    ranked: list[SearchCandidate] = []

    for candidate in candidates:
        if not candidate.image_url:
            candidate.status = "NO_IMAGE_URL"
            ranked.append(candidate)
            continue

        try:
            candidate.downloaded_image = download_candidate_image(candidate.image_url)
            score = best_face_similarity(
                engine,
                target_embedding,
                candidate.downloaded_image,
                max_faces=config.max_faces_per_candidate,
            )
            candidate.face_similarity = score
            candidate.status = (
                "MATCH" if score is not None and score >= config.threshold else "NO_MATCH"
            )
        except Exception as exc:
            candidate.status = f"SKIPPED: {type(exc).__name__}"

        ranked.append(candidate)

    ranked.sort(key=lambda c: c.face_similarity if c.face_similarity is not None else -1.0, reverse=True)
    return ranked
