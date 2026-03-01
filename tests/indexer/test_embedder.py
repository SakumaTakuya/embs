from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np

from embs.indexer.embedder import MODEL_NAME, Embedder


class TestEmbedder:
    @patch("embs.indexer.embedder.SentenceTransformer")
    def test_init_default_model(self, mock_st_cls):
        embedder = Embedder()

        assert embedder.model_name == MODEL_NAME
        mock_st_cls.assert_called_once_with(MODEL_NAME)

    @patch("embs.indexer.embedder.SentenceTransformer")
    def test_init_custom_model(self, mock_st_cls):
        embedder = Embedder(model_name="custom/model")

        assert embedder.model_name == "custom/model"
        mock_st_cls.assert_called_once_with("custom/model")

    @patch("embs.indexer.embedder.SentenceTransformer")
    def test_embed_returns_ndarray(self, mock_st_cls):
        mock_model = MagicMock()
        expected = np.random.randn(2, 768).astype(np.float32)
        mock_model.encode.return_value = expected
        mock_st_cls.return_value = mock_model

        embedder = Embedder()
        result = embedder.embed(["text1", "text2"])

        assert isinstance(result, np.ndarray)
        assert result.shape == (2, 768)

    @patch("embs.indexer.embedder.SentenceTransformer")
    def test_embed_calls_encode_with_normalize(self, mock_st_cls):
        mock_model = MagicMock()
        mock_model.encode.return_value = np.zeros((1, 768), dtype=np.float32)
        mock_st_cls.return_value = mock_model

        embedder = Embedder()
        embedder.embed(["test"])

        mock_model.encode.assert_called_once_with(
            ["test"], normalize_embeddings=True
        )
