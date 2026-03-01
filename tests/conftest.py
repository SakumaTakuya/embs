from __future__ import annotations

import numpy as np
import pytest


@pytest.fixture
def sample_embedding():
    """768次元の正規化済みサンプルembedding"""
    rng = np.random.default_rng(42)
    vec = rng.standard_normal(768).astype(np.float32)
    return vec / np.linalg.norm(vec)


@pytest.fixture
def sample_candidates():
    """検索候補のサンプルリスト"""
    return [
        {
            "id": 1,
            "distance": 0.1,
            "source_file": "doc1.md",
            "chunk_index": 0,
            "text": "テスト文書1",
        },
        {
            "id": 2,
            "distance": 0.2,
            "source_file": "doc2.md",
            "chunk_index": 0,
            "text": "テスト文書2",
        },
        {
            "id": 3,
            "distance": 0.3,
            "source_file": "doc3.md",
            "chunk_index": 1,
            "text": "テスト文書3",
        },
    ]
