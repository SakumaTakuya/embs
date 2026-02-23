from __future__ import annotations

import sys
from pathlib import Path

from embs.indexer.embedder import Embedder, MODEL_NAME
from embs.indexer.store import VectorStore
from embs.searcher.reranker import Reranker


def search(
    query: str,
    db_path: Path,
    top_k: int = 5,
    initial_k: int = 20,
) -> list[dict]:
    """セマンティック検索を実行する

    1. クエリをembedding化
    2. sqlite-vecでコサイン類似度検索（上位initial_k件）
    3. rerankerで上位top_k件に絞り込み
    """
    store = VectorStore(db_path)

    # モデル名の整合性チェック
    stored_model = store.get_model_name()
    if stored_model and stored_model != MODEL_NAME:
        print(
            f"警告: インデックスのembeddingモデル({stored_model})が"
            f"現在のモデル({MODEL_NAME})と異なります",
            file=sys.stderr,
        )

    embedder = Embedder()
    query_embedding = embedder.embed([query])[0]

    candidates = store.search(query_embedding, top_k=initial_k)
    store.close()

    reranker = Reranker()
    results = reranker.rerank(query, candidates, top_k=top_k)

    return results
