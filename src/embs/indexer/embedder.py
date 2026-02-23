from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "pkshatech/GLuCoSE-base-ja-v2"


class Embedder:
    """GLuCoSE-base-ja-v2によるembedding生成"""

    def __init__(self, model_name: str = MODEL_NAME) -> None:
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed(self, texts: list[str]) -> np.ndarray:
        """テキストのリストをembeddingに変換する"""
        return self.model.encode(texts, normalize_embeddings=True)
