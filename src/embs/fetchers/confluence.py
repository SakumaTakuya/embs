from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
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
    """Confluence取得の設定"""

    space: str | None = None
    pages: list[PageConfig] | None = None


def load_confluence_config(config_path: Path) -> ConfluenceConfig:
    """JSONファイルからConfluence取得設定を読み込む

    JSON format::

        {
          "space": "ENG",
          "pages": [
            {"page_id": "12345", "include_descendants": true},
            {"page_id": "67890"}
          ]
        }

    ``space`` と ``pages`` は両方指定可能。少なくとも一方が必要。
    """
    with open(config_path, encoding="utf-8") as f:
        data = json.load(f)

    pages = [
        PageConfig(
            page_id=str(p["page_id"]),
            include_descendants=p.get("include_descendants", False),
        )
        for p in data.get("pages", [])
    ] or None

    return ConfluenceConfig(space=data.get("space"), pages=pages)


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
        page_configs: list[PageConfig] | None = None,
    ) -> None:
        self.url = url or os.environ["CONFLUENCE_URL"]
        self.token = token or os.environ["CONFLUENCE_TOKEN"]
        self.space_key = space_key
        self.page_configs = page_configs

        if not self.space_key and not self.page_configs:
            self.space_key = os.environ.get("CONFLUENCE_SPACE_KEY")

    def fetch(self, out_dir: Path) -> list[Path]:
        out_dir.mkdir(parents=True, exist_ok=True)

        confluence = Confluence(url=self.url, token=self.token)
        converter = DocumentConverter()

        pages: list[dict] = []
        seen_ids: set[str] = set()

        if self.space_key:
            for p in confluence.get_all_pages_from_space(
                self.space_key,
                expand="body.storage",
                limit=100,
            ):
                pid = str(p["id"])
                if pid not in seen_ids:
                    pages.append(p)
                    seen_ids.add(pid)

        if self.page_configs:
            for p in self._collect_pages_by_config(confluence):
                pid = str(p["id"])
                if pid not in seen_ids:
                    pages.append(p)
                    seen_ids.add(pid)

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

    # -- private helpers --------------------------------------------------

    def _collect_pages_by_config(
        self, confluence: Confluence
    ) -> list[dict]:
        """ページ設定に基づいてページを収集する（重複排除付き）"""
        pages: list[dict] = []
        seen_ids: set[str] = set()

        for cfg in self.page_configs:
            # 指定ページ自体を取得
            page = confluence.get_page_by_id(
                cfg.page_id, expand="body.storage"
            )
            pid = str(page["id"])
            if pid not in seen_ids:
                pages.append(page)
                seen_ids.add(pid)

            # 子孫ページを取得
            if cfg.include_descendants:
                for desc in self._fetch_descendants(confluence, cfg.page_id):
                    did = str(desc["id"])
                    if did not in seen_ids:
                        pages.append(desc)
                        seen_ids.add(did)

        return pages

    def _fetch_descendants(
        self, confluence: Confluence, page_id: str
    ) -> list[dict]:
        """CQLのancestorオペレータで全子孫ページを取得する"""
        pages: list[dict] = []
        start = 0
        limit = 100
        while True:
            response = confluence.cql(
                f"ancestor = {page_id} AND type = page",
                expand="body.storage",
                start=start,
                limit=limit,
            )
            batch = response.get("results", [])
            pages.extend(batch)
            if len(batch) < limit:
                break
            start += limit
        return pages
