import numpy as np

from app.face import cosine_similarity
from app.matcher import MatchConfig


def test_cosine_similarity_identical_vectors():
    a = np.array([1.0, 0.0, 0.0])
    assert cosine_similarity(a, a) == 1.0


def test_match_threshold_is_configurable():
    config = MatchConfig(threshold=0.72)
    assert config.threshold == 0.72
