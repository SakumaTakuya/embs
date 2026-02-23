from __future__ import annotations

from sentence_transformers import CrossEncoder

MODEL_NAME = "hotchpotch/japanese-reranker-cross-encoder-large-v1"


class Reranker:
    """japanese-reranker-cross-encoderによるリランキング"""

    def __init__(self, model_name: str = MODEL_NAME) -> None:
        self.model = CrossEncoder(model_name)

    def rerank(
        self, query: str, candidates: list[dict], top_k: int = 5
    ) -> list[dict]:
        """候補をクエリとの関連度で並び替え、上位k件を返す"""
        if not candidates:
            return []

        pairs = [(query, c["text"]) for c in candidates]
        scores = self.model.predict(pairs)

        for candidate, score in zip(candidates, scores):
            candidate["rerank_score"] = float(score)

        ranked = sorted(candidates, key=lambda c: c["rerank_score"], reverse=True)
        return ranked[:top_k]
