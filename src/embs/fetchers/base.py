from abc import ABC, abstractmethod
from pathlib import Path


class BaseFetcher(ABC):
    @abstractmethod
    def fetch(self, out_dir: Path) -> list[Path]:
        """Markdownファイルのリストを返す"""
        ...
