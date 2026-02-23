# embs プロジェクト原則 (CONSTITUTION)

本ドキュメントは embs プロジェクトにおける最上位の原則を定義する。
すべての仕様書・設計書・実装はこの原則に準拠しなければならない。

---

## 1. プロジェクトビジョン

**embs** は、日本語テキストに対するセマンティック検索CLIツールである。
fuzzy検索では対応できない「意味に基づく検索」を、ローカル環境で手軽に利用可能にすることを目的とする。

### 1.1. コアバリュー

- **意味検索の民主化**: 専門知識がなくても `uvx embs search "..."` で意味ベースの検索が使える
- **日本語ファースト**: 日本語テキストに最適化されたモデルとパイプラインを採用する
- **シンプルなCLI体験**: fetch → index → search の3ステップで完結する
- **ローカル完結**: ベクトルDBにsqlite-vecを採用し、外部サービスへの依存を最小化する

---

## 2. アーキテクチャ原則

### 2.1. 二段階パイプライン

システムは以下の2段階で構成される。この分離は維持しなければならない。

1. **fetch**: ドキュメントソースからMarkdownファイルを取得する
2. **index**: MarkdownファイルをチャンキングしてembeddingをDBに保存する

検索は index で作成されたDBに対して実行する。

### 2.2. Fetcher拡張性

- ドキュメントソースは `BaseFetcher` を継承して追加する
- 各Fetcherの出力はMarkdownファイルに統一する
- fetch と index は疎結合を維持し、Markdownファイルを中間形式とする

### 2.3. 単一DBファイル

- インデックスは単一の SQLite ファイル（sqlite-vec）に格納する
- DBファイルはポータブルであり、コピーするだけで別環境に移行可能とする

---

## 3. 技術スタック

以下の技術選定はプロジェクトの根幹であり、変更する場合は本ドキュメントの改訂を要する。

| 領域 | 採用技術 | 選定理由 |
|------|----------|----------|
| 言語 | Python ≥ 3.11 | ML/NLPエコシステムとの親和性 |
| パッケージ管理 | uv | 高速な依存解決、uvx による手軽な実行 |
| CLI | typer | 型アノテーションベースの宣言的CLI定義 |
| ドキュメント変換・チャンキング | docling | HTML/PDF→Markdown変換、HierarchicalChunkerによる構造化チャンキング |
| embedding | pkshatech/GLuCoSE-base-ja-v2 | 日本語に最適化されたsentence embedding |
| reranker | hotchpotch/japanese-reranker-cross-encoder-large-v1 | 日本語に最適化されたcross-encoder |
| ベクトルDB | sqlite-vec | SQLite拡張によるベクトル検索、外部サーバー不要 |
| Confluence連携 | atlassian-python-api | 公式REST APIラッパー |

---

## 4. 開発標準

### 4.1. コード規約

- Python 3.11+ の型ヒントを使用する
- `from __future__ import annotations` を各モジュールの先頭に配置する
- フォーマッターおよびリンターの設定はプロジェクトルートの設定ファイルに従う

### 4.2. モジュール構成

```
src/embs/
├── cli.py          # CLIエントリポイント（typer）
├── fetchers/       # ドキュメント取得（BaseFetcher実装）
├── indexer/        # チャンキング・embedding・ベクトル保存
└── searcher/       # 検索・リランキング
```

- 各サブパッケージは単一の責務を持つ
- パッケージ間の依存方向: `cli → fetchers / indexer / searcher`、`searcher → indexer`（モデル名参照）

### 4.3. ビルドシステム

- `pyproject.toml` + hatchling をビルドバックエンドとする
- エントリポイント: `embs = "embs.cli:app"`

---

## 5. 品質基準

### 5.1. テスト

- 新規機能にはユニットテストを作成する
- 外部サービス（Confluence API、MLモデルロード）はモック化してテストする

### 5.2. セキュリティ

- APIトークンやクレデンシャルはソースコードにハードコードしない
- 外部サービスの認証情報は環境変数経由で取得する（`CONFLUENCE_URL`, `CONFLUENCE_TOKEN`, `CONFLUENCE_SPACE_KEY`）

### 5.3. パフォーマンス

- embedding生成とreranking はバッチ処理を活用する
- sqlite-vec のベクトル検索で候補を絞り込み、cross-encoder reranker で精度を上げる二段階検索を維持する

---

## 6. ドキュメント規約

- プロジェクトドキュメントは AI-SDD ワークフロー（v3.1.0）に従う
- ドキュメント言語は日本語を基本とする
- ユーザー向けメッセージ（CLIの出力）は日本語とする

---

## 7. スコープ

### 7.1. 現在のスコープ

- Confluenceおよびローカルディレクトリからのドキュメント取得
- Markdownベースのチャンキングとembedding生成
- コサイン類似度検索 + cross-encoder reranking
- CLIインターフェース

### 7.2. スコープ外（将来検討）

- Web UI / API サーバー
- リアルタイムインデックス更新
- 多言語対応（日本語以外）
- クラウドベクトルDB連携
