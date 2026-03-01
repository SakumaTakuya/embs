from __future__ import annotations

from embs.fetchers.markdown import MarkdownFetcher


class TestMarkdownFetcher:
    def test_fetch_copies_md_files(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        (source / "doc1.md").write_text("# Doc 1", encoding="utf-8")
        (source / "doc2.md").write_text("# Doc 2", encoding="utf-8")

        out = tmp_path / "output"
        fetcher = MarkdownFetcher(source)
        result = fetcher.fetch(out)

        assert len(result) == 2
        assert (out / "doc1.md").exists()
        assert (out / "doc2.md").exists()
        assert (out / "doc1.md").read_text(encoding="utf-8") == "# Doc 1"

    def test_fetch_preserves_directory_structure(self, tmp_path):
        source = tmp_path / "source"
        (source / "sub" / "deep").mkdir(parents=True)
        (source / "root.md").write_text("root", encoding="utf-8")
        (source / "sub" / "nested.md").write_text("nested", encoding="utf-8")
        (source / "sub" / "deep" / "deep.md").write_text("deep", encoding="utf-8")

        out = tmp_path / "output"
        fetcher = MarkdownFetcher(source)
        fetcher.fetch(out)

        assert (out / "root.md").exists()
        assert (out / "sub" / "nested.md").exists()
        assert (out / "sub" / "deep" / "deep.md").exists()

    def test_fetch_ignores_non_md_files(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        (source / "doc.md").write_text("markdown", encoding="utf-8")
        (source / "image.png").write_bytes(b"\x89PNG")
        (source / "notes.txt").write_text("text", encoding="utf-8")

        out = tmp_path / "output"
        fetcher = MarkdownFetcher(source)
        result = fetcher.fetch(out)

        assert len(result) == 1
        assert not (out / "image.png").exists()
        assert not (out / "notes.txt").exists()

    def test_fetch_empty_directory(self, tmp_path):
        source = tmp_path / "empty"
        source.mkdir()

        out = tmp_path / "output"
        fetcher = MarkdownFetcher(source)
        result = fetcher.fetch(out)

        assert result == []

    def test_fetch_creates_output_directory(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        (source / "doc.md").write_text("test", encoding="utf-8")

        out = tmp_path / "new" / "nested" / "output"
        fetcher = MarkdownFetcher(source)
        fetcher.fetch(out)

        assert out.exists()
        assert (out / "doc.md").exists()
