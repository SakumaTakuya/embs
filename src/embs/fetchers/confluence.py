from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

from atlassian import Confluence
from docling.document_converter import DocumentConverter

from embs.fetchers.base import BaseFetcher


def _sanitize_filename(name: str) -> str:
    """ファイル名に使えない文字を除去する"""
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()


@dataclass
class PageConfig:
    """個別ページの取得設定"""

    page_id: str
    include_descendants: bool = False


def load_page_configs(config_path: Path) -> list[PageConfig]:
    """JSON設定ファイルからページ設定を読み込む"""
    data = json.loads(config_path.read_text(encoding="utf-8"))
    pages = data.get("pages", [])
    return [
        PageConfig(
            page_id=str(p["page_id"]),
            include_descendants=p.get("include_descendants", False),
        )
        for p in pages
    ]


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
            if not self.space_key:
                raise ValueError(
                    "space_key または page_configs のいずれかを指定してください"
                )

    def fetch(self, out_dir: Path) -> list[Path]:
        out_dir.mkdir(parents=True, exist_ok=True)

        confluence = Confluence(url=self.url, token=self.token)
        converter = DocumentConverter()

        if self.page_configs:
            pages = self._collect_pages_from_configs(confluence)
        else:
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

    def _collect_pages_from_configs(
        self, confluence: Confluence
    ) -> list[dict]:
        """ページ設定に基づいてページを収集する"""
        pages: list[dict] = []
        seen_ids: set[str] = set()

        for config in self.page_configs:
            self._collect_page(confluence, config.page_id, seen_ids, pages)
            if config.include_descendants:
                self._collect_descendants(
                    confluence, config.page_id, seen_ids, pages
                )

        return pages

    def _collect_page(
        self,
        confluence: Confluence,
        page_id: str,
        seen_ids: set[str],
        pages: list[dict],
    ) -> None:
        """単一ページを取得してリストに追加する（重複スキップ）"""
        if page_id in seen_ids:
            return
        page = confluence.get_page_by_id(page_id, expand="body.storage")
        seen_ids.add(page_id)
        pages.append(page)

    def _collect_descendants(
        self,
        confluence: Confluence,
        page_id: str,
        seen_ids: set[str],
        pages: list[dict],
    ) -> None:
        """子孫ページを再帰的に取得する"""
        children = confluence.get_page_child_by_type(
            page_id, type="page", start=0, limit=100
        )
        for child in children:
            child_id = str(child["id"])
            self._collect_page(confluence, child_id, seen_ids, pages)
            self._collect_descendants(confluence, child_id, seen_ids, pages)
