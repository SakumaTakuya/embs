from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np

from embs.searcher.query import search


class TestSearch:
    @patch("embs.searcher.query.Reranker")
    @patch("embs.searcher.query.Embedder")
    @patch("embs.searcher.query.VectorStore")
    def test_search_pipeline(self, mock_store_cls, mock_embedder_cls, mock_reranker_cls):
        # VectorStoreのモック
        mock_store = MagicMock()
        mock_store.get_model_name.return_value = "pkshatech/GLuCoSE-base-ja-v2"
        mock_store.search.return_value = [
            {"id": 1, "distance": 0.1, "source_file": "a.md", "chunk_index": 0, "text": "text1"},
        ]
        mock_store_cls.return_value = mock_store

        # Embedderのモック
        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = np.zeros((1, 768), dtype=np.float32)
        mock_embedder_cls.return_value = mock_embedder

        # Rerankerのモック
        mock_reranker = MagicMock()
        mock_reranker.rerank.return_value = [
            {"id": 1, "distance": 0.1, "source_file": "a.md", "chunk_index": 0, "text": "text1", "rerank_score": 0.9},
        ]
        mock_reranker_cls.return_value = mock_reranker

        result = search("test query", "dummy.db", top_k=5)

        # パイプラインの各ステップが呼ばれたことを確認
        mock_embedder.embed.assert_called_once_with(["test query"])
        mock_store.search.assert_called_once()
        mock_reranker.rerank.assert_called_once()
        mock_store.close.assert_called_once()

        assert len(result) == 1
        assert result[0]["rerank_score"] == 0.9

    @patch("embs.searcher.query.Reranker")
    @patch("embs.searcher.query.Embedder")
    @patch("embs.searcher.query.VectorStore")
    def test_search_model_mismatch_warning(
        self, mock_store_cls, mock_embedder_cls, mock_reranker_cls, capsys
    ):
        mock_store = MagicMock()
        mock_store.get_model_name.return_value = "old-model/v1"
        mock_store.search.return_value = []
        mock_store_cls.return_value = mock_store

        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = np.zeros((1, 768), dtype=np.float32)
        mock_embedder_cls.return_value = mock_embedder

        mock_reranker = MagicMock()
        mock_reranker.rerank.return_value = []
        mock_reranker_cls.return_value = mock_reranker

        search("query", "dummy.db")

        captured = capsys.readouterr()
        assert "警告" in captured.err
        assert "old-model/v1" in captured.err

    @patch("embs.searcher.query.Reranker")
    @patch("embs.searcher.query.Embedder")
    @patch("embs.searcher.query.VectorStore")
    def test_search_model_match_no_warning(
        self, mock_store_cls, mock_embedder_cls, mock_reranker_cls, capsys
    ):
        mock_store = MagicMock()
        mock_store.get_model_name.return_value = "pkshatech/GLuCoSE-base-ja-v2"
        mock_store.search.return_value = []
        mock_store_cls.return_value = mock_store

        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = np.zeros((1, 768), dtype=np.float32)
        mock_embedder_cls.return_value = mock_embedder

        mock_reranker = MagicMock()
        mock_reranker.rerank.return_value = []
        mock_reranker_cls.return_value = mock_reranker

        search("query", "dummy.db")

        captured = capsys.readouterr()
        assert "警告" not in captured.err

    @patch("embs.searcher.query.Reranker")
    @patch("embs.searcher.query.Embedder")
    @patch("embs.searcher.query.VectorStore")
    def test_search_passes_initial_k_to_store(
        self, mock_store_cls, mock_embedder_cls, mock_reranker_cls
    ):
        mock_store = MagicMock()
        mock_store.get_model_name.return_value = None
        mock_store.search.return_value = []
        mock_store_cls.return_value = mock_store

        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = np.zeros((1, 768), dtype=np.float32)
        mock_embedder_cls.return_value = mock_embedder

        mock_reranker = MagicMock()
        mock_reranker.rerank.return_value = []
        mock_reranker_cls.return_value = mock_reranker

        search("query", "dummy.db", top_k=3, initial_k=50)

        mock_store.search.assert_called_once()
        _, kwargs = mock_store.search.call_args
        assert kwargs["top_k"] == 50
