from __future__ import annotations

import os
import re
from pathlib import Path

from atlassian import Confluence
from docling.document_converter import DocumentConverter

from embs.fetchers.base import BaseFetcher


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
        space_key: str | None = None,
    ) -> None:
        self.url = url or os.environ["CONFLUENCE_URL"]
        self.token = token or os.environ["CONFLUENCE_TOKEN"]
        self.space_key = space_key or os.environ["CONFLUENCE_SPACE_KEY"]

    def fetch(self, out_dir: Path) -> list[Path]:
        out_dir.mkdir(parents=True, exist_ok=True)

        confluence = Confluence(url=self.url, token=self.token)
        converter = DocumentConverter()

        pages = confluence.get_all_pages_from_space(
            self.space_key,
            expand="body.storage",
            limit=100,
        )

        saved: list[Path] = []
        for page in pages:
            page_id = page["id"]
            title = page["title"]
            html_body = page["body"]["storage"]["value"]

            # doclingでHTMLからMarkdownへ変換
            result = converter.convert_html(html_body)
            md_text = result.document.export_to_markdown()

            filename = f"{page_id}_{_sanitize_filename(title)}.md"
            dest = out_dir / filename
            dest.write_text(md_text, encoding="utf-8")
            saved.append(dest)

        return saved
