from __future__ import annotations

import sqlite3
import struct
from pathlib import Path

import numpy as np
import sqlite_vec


EMBEDDING_DIM = 768


def _serialize_f32(vec: np.ndarray) -> bytes:
    """numpy arrayをsqlite-vec用のバイナリに変換する"""
    return struct.pack(f"{len(vec)}f", *vec.tolist())


class VectorStore:
    """sqlite-vecベースのベクトルストア"""

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.enable_load_extension(True)
        sqlite_vec.load(self.conn)
        self.conn.enable_load_extension(False)

    def create_tables(self, model_name: str) -> None:
        """テーブルを作成する"""
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                text TEXT NOT NULL
            )
            """
        )
        cur.execute(
            f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0 (
                embedding float[{EMBEDDING_DIM}]
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            INSERT OR REPLACE INTO metadata (key, value) VALUES ('model_name', ?)
            """,
            (model_name,),
        )
        self.conn.commit()

    def get_model_name(self) -> str | None:
        """保存されたembeddingモデル名を取得する"""
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT value FROM metadata WHERE key = 'model_name'")
            row = cur.fetchone()
            return row[0] if row else None
        except sqlite3.OperationalError:
            return None

    def insert(
        self,
        source_file: str,
        chunk_index: int,
        text: str,
        embedding: np.ndarray,
    ) -> None:
        """チャンクとembeddingを挿入する"""
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO chunks (source_file, chunk_index, text) VALUES (?, ?, ?)",
            (source_file, chunk_index, text),
        )
        rowid = cur.lastrowid
        cur.execute(
            "INSERT INTO vec_chunks (rowid, embedding) VALUES (?, ?)",
            (rowid, _serialize_f32(embedding)),
        )
        self.conn.commit()

    def search(
        self, query_embedding: np.ndarray, top_k: int = 20
    ) -> list[dict]:
        """コサイン類似度で上位k件を検索する"""
        cur = self.conn.cursor()
        rows = cur.execute(
            """
            SELECT
                v.rowid,
                v.distance,
                c.source_file,
                c.chunk_index,
                c.text
            FROM vec_chunks v
            INNER JOIN chunks c ON c.id = v.rowid
            WHERE v.embedding MATCH ?
            ORDER BY v.distance
            LIMIT ?
            """,
            (_serialize_f32(query_embedding), top_k),
        ).fetchall()

        results = []
        for row in rows:
            results.append(
                {
                    "id": row[0],
                    "distance": row[1],
                    "source_file": row[2],
                    "chunk_index": row[3],
                    "text": row[4],
                }
            )
        return results

    def close(self) -> None:
        self.conn.close()
