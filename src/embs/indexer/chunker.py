from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker.hierarchical_chunker import HierarchicalChunker


@dataclass
class Chunk:
    text: str
    source_file: str
    chunk_index: int


def chunk_markdown(path: Path) -> list[Chunk]:
    """Markdownファイルをチャンクに分割する"""
    converter = DocumentConverter()
    result = converter.convert(str(path))
    doc = result.document

    chunker = HierarchicalChunker()
    chunks: list[Chunk] = []
    for i, chunk in enumerate(chunker.chunk(doc)):
        text = chunk.text
        if text.strip():
            chunks.append(Chunk(text=text, source_file=path.name, chunk_index=i))

    return chunks
