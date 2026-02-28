from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from atlassian import Confluence
from docling.document_converter import DocumentConverter

from embs.fetchers.base import BaseFetcher


@dataclass
class PageConfig:
    """個別ページの取得設定"""

    page_id: str
    include_descendants: bool = False


@dataclass
class ConfluenceConfig:
    """Confluence取得設定"""

    space_key: str
    pages: list[PageConfig] = field(default_factory=list)


def load_config(path: Path) -> ConfluenceConfig:
    """JSONファイルからConfluence設定を読み込む"""
    data = json.loads(path.read_text(encoding="utf-8"))

    space_key = data["space_key"]
    pages = [
        PageConfig(
            page_id=str(p["page_id"]),
            include_descendants=p.get("include_descendants", False),
        )
        for p in data.get("pages", [])
    ]
    return ConfluenceConfig(space_key=space_key, pages=pages)


def _sanitize_filename(name: str) -> str:
    """ファイル名に使えない文字を除去する"""
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()


class ConfluenceFetcher(BaseFetcher):
    """Confluence APIからページを取得しMarkdownに変換する"""

    def __init__(
        self,
        *,
        url: str | None = None,
        token: str | None = None,
    ) -> None:
        self.url = url or os.environ["CONFLUENCE_URL"]
        self.token = token or os.environ["CONFLUENCE_TOKEN"]

    def fetch(self, out_dir: Path, config: ConfluenceConfig) -> list[Path]:
        """設定ファイルに基づいて特定ページを取得する"""
        out_dir.mkdir(parents=True, exist_ok=True)

        confluence = Confluence(url=self.url, token=self.token)
        converter = DocumentConverter()

        saved: list[Path] = []
        for page_cfg in config.pages:
            page = confluence.get_page_by_id(
                page_cfg.page_id, expand="body.storage"
            )
            self._save_page(page, converter, out_dir, saved)

            if page_cfg.include_descendants:
                self._fetch_descendants(
                    confluence, converter, page_cfg.page_id, out_dir, saved
                )

        return saved

    def _fetch_descendants(
        self,
        confluence: Confluence,
        converter: DocumentConverter,
        page_id: str,
        out_dir: Path,
        saved: list[Path],
    ) -> None:
        """子孫ページを再帰的に取得する"""
        children = confluence.get_page_child_by_type(
            page_id, type="page", expand="body.storage"
        )
        for child in children:
            self._save_page(child, converter, out_dir, saved)
            self._fetch_descendants(
                confluence, converter, child["id"], out_dir, saved
            )

    @staticmethod
    def _save_page(
        page: dict,
        converter: DocumentConverter,
        out_dir: Path,
        saved: list[Path],
    ) -> None:
        """ページをMarkdownに変換して保存する"""
        page_id = page["id"]
        title = page["title"]
        html_body = page["body"]["storage"]["value"]

        result = converter.convert_html(html_body)
        md_text = result.document.export_to_markdown()

        filename = f"{page_id}_{_sanitize_filename(title)}.md"
        dest = out_dir / filename
        dest.write_text(md_text, encoding="utf-8")
        saved.append(dest)
