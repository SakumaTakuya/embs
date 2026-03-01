from __future__ import annotations

from unittest.mock import MagicMock, patch

from embs.indexer.chunker import Chunk, chunk_markdown


class TestChunkDataclass:
    def test_fields(self):
        chunk = Chunk(text="hello", source_file="test.md", chunk_index=0)

        assert chunk.text == "hello"
        assert chunk.source_file == "test.md"
        assert chunk.chunk_index == 0


class TestChunkMarkdown:
    def _make_mock_chunk(self, text):
        mock = MagicMock()
        mock.text = text
        return mock

    @patch("embs.indexer.chunker.HierarchicalChunker")
    @patch("embs.indexer.chunker.DocumentConverter")
    def test_returns_chunks(self, mock_converter_cls, mock_chunker_cls, tmp_path):
        # DocumentConverterのモック
        mock_doc = MagicMock()
        mock_result = MagicMock()
        mock_result.document = mock_doc
        mock_converter_cls.return_value.convert.return_value = mock_result

        # HierarchicalChunkerのモック
        mock_chunker_cls.return_value.chunk.return_value = [
            self._make_mock_chunk("chunk 1"),
            self._make_mock_chunk("chunk 2"),
        ]

        md_file = tmp_path / "test.md"
        md_file.write_text("# Test", encoding="utf-8")

        result = chunk_markdown(md_file)

        assert len(result) == 2
        assert all(isinstance(c, Chunk) for c in result)

    @patch("embs.indexer.chunker.HierarchicalChunker")
    @patch("embs.indexer.chunker.DocumentConverter")
    def test_filters_empty_chunks(self, mock_converter_cls, mock_chunker_cls, tmp_path):
        mock_doc = MagicMock()
        mock_result = MagicMock()
        mock_result.document = mock_doc
        mock_converter_cls.return_value.convert.return_value = mock_result

        mock_chunker_cls.return_value.chunk.return_value = [
            self._make_mock_chunk("valid text"),
            self._make_mock_chunk("   "),  # 空白のみ
            self._make_mock_chunk(""),  # 空文字
            self._make_mock_chunk("another valid"),
        ]

        md_file = tmp_path / "test.md"
        md_file.write_text("# Test", encoding="utf-8")

        result = chunk_markdown(md_file)

        assert len(result) == 2
        assert result[0].text == "valid text"
        assert result[1].text == "another valid"

    @patch("embs.indexer.chunker.HierarchicalChunker")
    @patch("embs.indexer.chunker.DocumentConverter")
    def test_source_file_is_filename(self, mock_converter_cls, mock_chunker_cls, tmp_path):
        mock_doc = MagicMock()
        mock_result = MagicMock()
        mock_result.document = mock_doc
        mock_converter_cls.return_value.convert.return_value = mock_result

        mock_chunker_cls.return_value.chunk.return_value = [
            self._make_mock_chunk("text"),
        ]

        md_file = tmp_path / "subdir" / "document.md"
        md_file.parent.mkdir(parents=True)
        md_file.write_text("# Test", encoding="utf-8")

        result = chunk_markdown(md_file)

        # パス全体ではなくファイル名のみ
        assert result[0].source_file == "document.md"

    @patch("embs.indexer.chunker.HierarchicalChunker")
    @patch("embs.indexer.chunker.DocumentConverter")
    def test_chunk_index_tracks_original_position(
        self, mock_converter_cls, mock_chunker_cls, tmp_path
    ):
        mock_doc = MagicMock()
        mock_result = MagicMock()
        mock_result.document = mock_doc
        mock_converter_cls.return_value.convert.return_value = mock_result

        # index 0: valid, index 1: empty (filtered), index 2: valid
        mock_chunker_cls.return_value.chunk.return_value = [
            self._make_mock_chunk("first"),
            self._make_mock_chunk("   "),
            self._make_mock_chunk("third"),
        ]

        md_file = tmp_path / "test.md"
        md_file.write_text("# Test", encoding="utf-8")

        result = chunk_markdown(md_file)

        # chunk_indexは元のenumerateのインデックスを保持
        assert result[0].chunk_index == 0
        assert result[1].chunk_index == 2
