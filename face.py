from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np


@dataclass
class FaceResult:
    bbox: tuple[int, int, int, int]
    detection_score: float
    embedding: np.ndarray


class FaceEngine:
    """InsightFace-based face detection and embedding engine."""

    def __init__(self, model_name: str = "buffalo_l", det_size: tuple[int, int] = (640, 640)):
        try:
            from insightface.app import FaceAnalysis
        except ImportError as exc:
            raise RuntimeError(
                "InsightFace is not installed. Run: pip install insightface onnxruntime"
            ) from exc

        self._app = FaceAnalysis(
            name=model_name,
            providers=["CPUExecutionProvider"],
        )
        self._app.prepare(ctx_id=0, det_size=det_size)

    @staticmethod
    def load_image(image_path: str | Path) -> np.ndarray:
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Could not read image: {image_path}")
        return image

    def detect(self, image: np.ndarray) -> List[FaceResult]:
        faces = self._app.get(image)
        results: List[FaceResult] = []
        for face in faces:
            x1, y1, x2, y2 = [int(v) for v in face.bbox]
            results.append(
                FaceResult(
                    bbox=(x1, y1, x2, y2),
                    detection_score=float(face.det_score),
                    embedding=np.asarray(face.embedding, dtype=np.float32),
                )
            )
        return results

    def detect_from_path(self, image_path: str | Path) -> tuple[np.ndarray, List[FaceResult]]:
        image = self.load_image(image_path)
        return image, self.detect(image)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=np.float32).reshape(-1)
    b = np.asarray(b, dtype=np.float32).reshape(-1)
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def select_primary_face(faces: List[FaceResult], index: int = 0) -> FaceResult:
    if not faces:
        raise ValueError("No face detected.")
    if index < 0 or index >= len(faces):
        raise IndexError(f"Face index {index} is out of range; detected {len(faces)} face(s).")
    return faces[index]
