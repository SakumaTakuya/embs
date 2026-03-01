from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from embs.fetchers.confluence import (
    ConfluenceConfig,
    ConfluenceFetcher,
    PageConfig,
    _sanitize_filename,
    load_config,
)


class TestLoadConfig:
    def test_basic(self, tmp_path):
        config_data = {
            "space_key": "TEAM",
            "pages": [
                {"page_id": "12345"},
            ],
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data), encoding="utf-8")

        result = load_config(config_file)

        assert isinstance(result, ConfluenceConfig)
        assert result.space_key == "TEAM"
        assert len(result.pages) == 1
        assert result.pages[0].page_id == "12345"
        assert result.pages[0].include_descendants is False

    def test_include_descendants(self, tmp_path):
        config_data = {
            "space_key": "DEV",
            "pages": [
                {"page_id": "111", "include_descendants": True},
                {"page_id": "222", "include_descendants": False},
            ],
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data), encoding="utf-8")

        result = load_config(config_file)

        assert result.pages[0].include_descendants is True
        assert result.pages[1].include_descendants is False

    def test_no_pages(self, tmp_path):
        config_data = {"space_key": "EMPTY"}
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data), encoding="utf-8")

        result = load_config(config_file)

        assert result.pages == []

    def test_page_id_converted_to_str(self, tmp_path):
        config_data = {
            "space_key": "TEAM",
            "pages": [{"page_id": 99999}],
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data), encoding="utf-8")

        result = load_config(config_file)

        assert result.pages[0].page_id == "99999"
        assert isinstance(result.pages[0].page_id, str)


class TestSanitizeFilename:
    def test_removes_forbidden_chars(self):
        assert _sanitize_filename('test\\file/name*?.md') == "test_file_name__.md"

    def test_replaces_colons_and_quotes(self):
        assert _sanitize_filename('file:"name"') == "file__name_"

    def test_replaces_angle_brackets_and_pipe(self):
        assert _sanitize_filename("a<b>c|d") == "a_b_c_d"

    def test_strips_whitespace(self):
        assert _sanitize_filename("  hello  ") == "hello"

    def test_normal_name_unchanged(self):
        assert _sanitize_filename("normal-file_name.md") == "normal-file_name.md"

    def test_empty_string(self):
        assert _sanitize_filename("") == ""


class TestConfluenceFetcherInit:
    def test_init_with_args(self):
        with patch("embs.fetchers.confluence.Confluence"):
            fetcher = ConfluenceFetcher(
                url="https://wiki.example.com",
                token="secret-token",
            )

        assert fetcher.url == "https://wiki.example.com"
        assert fetcher.token == "secret-token"

    def test_init_from_env(self, monkeypatch):
        monkeypatch.setenv("CONFLUENCE_URL", "https://env.example.com")
        monkeypatch.setenv("CONFLUENCE_TOKEN", "env-token")

        with patch("embs.fetchers.confluence.Confluence"):
            fetcher = ConfluenceFetcher()

        assert fetcher.url == "https://env.example.com"
        assert fetcher.token == "env-token"

    def test_init_missing_env_raises(self, monkeypatch):
        monkeypatch.delenv("CONFLUENCE_URL", raising=False)
        monkeypatch.delenv("CONFLUENCE_TOKEN", raising=False)

        with pytest.raises(KeyError):
            ConfluenceFetcher()
