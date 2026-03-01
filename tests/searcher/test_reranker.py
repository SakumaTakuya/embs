from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np

from embs.searcher.reranker import Reranker


class TestReranker:
    def _make_reranker(self, predict_scores):
        """モック済みRerankerを作成するヘルパー"""
        with patch("embs.searcher.reranker.CrossEncoder") as mock_cls:
            mock_model = MagicMock()
            mock_model.predict.return_value = np.array(predict_scores)
            mock_cls.return_value = mock_model
            reranker = Reranker()
        return reranker

    def test_rerank_empty_candidates(self):
        reranker = self._make_reranker([])
        result = reranker.rerank("query", [], top_k=5)

        assert result == []

    def test_rerank_sorts_by_score(self, sample_candidates):
        # スコアを逆順に設定: doc3が最高、doc1が最低
        reranker = self._make_reranker([0.1, 0.5, 0.9])
        result = reranker.rerank("query", sample_candidates, top_k=3)

        assert result[0]["id"] == 3  # score 0.9
        assert result[1]["id"] == 2  # score 0.5
        assert result[2]["id"] == 1  # score 0.1

    def test_rerank_respects_top_k(self, sample_candidates):
        reranker = self._make_reranker([0.3, 0.1, 0.2])
        result = reranker.rerank("query", sample_candidates, top_k=2)

        assert len(result) == 2

    def test_rerank_adds_score_field(self, sample_candidates):
        reranker = self._make_reranker([0.8, 0.6, 0.4])
        result = reranker.rerank("query", sample_candidates, top_k=3)

        for item in result:
            assert "rerank_score" in item
            assert isinstance(item["rerank_score"], float)

    def test_rerank_score_values(self, sample_candidates):
        reranker = self._make_reranker([0.1, 0.9, 0.5])
        result = reranker.rerank("query", sample_candidates, top_k=3)

        # 最高スコアが先頭
        assert result[0]["rerank_score"] == 0.9
        assert result[1]["rerank_score"] == 0.5
        assert result[2]["rerank_score"] == 0.1
