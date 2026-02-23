from __future__ import annotations

import shutil
from pathlib import Path

from embs.fetchers.base import BaseFetcher


class MarkdownFetcher(BaseFetcher):
    """ローカルディレクトリからMarkdownファイルを収集する"""

    def __init__(self, source_dir: Path) -> None:
        self.source_dir = Path(source_dir)

    def fetch(self, out_dir: Path) -> list[Path]:
        out_dir.mkdir(parents=True, exist_ok=True)

        saved: list[Path] = []
        for md_file in self.source_dir.rglob("*.md"):
            relative = md_file.relative_to(self.source_dir)
            dest = out_dir / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(md_file, dest)
            saved.append(dest)

        return saved
