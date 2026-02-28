from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(help="日本語テキストのセマンティック検索CLIツール")
fetch_app = typer.Typer(help="ドキュメントソースからMarkdownを取得")
app.add_typer(fetch_app, name="fetch")


@fetch_app.command("confluence")
def fetch_confluence(
    config: Path = typer.Option(..., "--config", help="設定ファイルパス (JSON)"),
    out: Path = typer.Option(..., "--out", help="出力ディレクトリ"),
) -> None:
    """設定ファイルに基づいてConfluenceからページを取得する"""
    from embs.fetchers.confluence import ConfluenceFetcher, load_config

    cfg = load_config(config)
    fetcher = ConfluenceFetcher()
    files = fetcher.fetch(out, cfg)
    typer.echo(f"{len(files)} ファイルを取得しました → {out}")


@fetch_app.command("markdown")
def fetch_markdown(
    source_dir: Path = typer.Argument(..., help="Markdownファイルのソースディレクトリ"),
    out: Path = typer.Option(..., "--out", help="出力ディレクトリ"),
) -> None:
    """ローカルディレクトリからMarkdownファイルを収集する"""
    from embs.fetchers.markdown import MarkdownFetcher

    fetcher = MarkdownFetcher(source_dir)
    files = fetcher.fetch(out)
    typer.echo(f"{len(files)} ファイルを取得しました → {out}")


@app.command("index")
def index(
    docs_dir: Path = typer.Argument(..., help="Markdownファイルのディレクトリ"),
    out: Path = typer.Option("index.db", "--out", help="出力DBファイルパス"),
) -> None:
    """MarkdownファイルからインデックスDBを作成する"""
    from embs.indexer.chunker import chunk_markdown
    from embs.indexer.embedder import Embedder
    from embs.indexer.store import VectorStore

    md_files = sorted(docs_dir.rglob("*.md"))
    if not md_files:
        typer.echo("Markdownファイルが見つかりませんでした", err=True)
        raise typer.Exit(1)

    typer.echo(f"{len(md_files)} ファイルを処理します...")

    embedder = Embedder()
    store = VectorStore(out)
    store.create_tables(model_name=embedder.model_name)

    total_chunks = 0
    for md_file in md_files:
        typer.echo(f"  {md_file.name}")
        chunks = chunk_markdown(md_file)
        for chunk in chunks:
            embedding = embedder.embed([chunk.text])[0]
            store.insert(
                source_file=chunk.source_file,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
                embedding=embedding,
            )
            total_chunks += 1

    store.close()
    typer.echo(f"完了: {total_chunks} チャンクをインデックス化 → {out}")


@app.command("search")
def search_cmd(
    query: str = typer.Argument(..., help="検索クエリ"),
    db: Path = typer.Option("index.db", "--db", help="インデックスDBファイルパス"),
    top_k: int = typer.Option(5, "--top-k", help="返す結果の数"),
) -> None:
    """セマンティック検索を実行する"""
    from embs.searcher.query import search

    if not db.exists():
        typer.echo(f"DBファイルが見つかりません: {db}", err=True)
        raise typer.Exit(1)

    results = search(query, db, top_k=top_k)

    if not results:
        typer.echo("結果が見つかりませんでした")
        return

    for i, r in enumerate(results, 1):
        typer.echo(f"\n--- [{i}] {r['source_file']} (score: {r['rerank_score']:.4f}) ---")
        typer.echo(r["text"])


if __name__ == "__main__":
    app()
