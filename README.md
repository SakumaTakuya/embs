# embs

日本語テキストのセマンティック検索CLIツール。fuzzy検索より曖昧な、意味ベースの検索を提供する。

## インストール

```bash
# uvxで直接実行（インストール不要）
uvx embs --help
```

## 使い方

### ドキュメント取得

```bash
# Confluenceからドキュメントを取得
uvx embs fetch confluence --space ENG --out ./docs/

# ローカルMarkdownファイルを収集
uvx embs fetch markdown ./local-docs/ --out ./docs/
```

### インデックス作成

```bash
uvx embs index ./docs/ --out engineering.db
```

### 検索

```bash
uvx embs search "エラーハンドリングの方法"
uvx embs search "デプロイ手順" --db engineering.db --top-k 10
```

## アーキテクチャ

### 二段階設計

```
【Stage 1: fetch】ドキュメントソース → Markdownファイル群
  - Confluence API → doclingでMarkdown変換 → .mdファイル保存
  - ローカル.mdファイル → そのままコピー

【Stage 2: index】Markdownファイル群 → index.db
  - docling HierarchicalChunkerでチャンキング
  - GLuCoSE-base-ja-v2でembedding生成
  - sqlite-vecにベクトルを保存
```

### 検索フロー

```
クエリ入力
  → GLuCoSE-base-ja-v2でembedding化
  → sqlite-vecでコサイン類似度検索（上位20件）
  → japanese-reranker-cross-encoderで上位5件に絞り込み
  → ファイル名・該当チャンク・スコアを表示
```

## 使用モデル・ライブラリ

| 用途 | モデル・ライブラリ |
|------|-------------------|
| ドキュメント解析・チャンキング | docling |
| embedding | pkshatech/GLuCoSE-base-ja-v2 |
| reranker | hotchpotch/japanese-reranker-cross-encoder-large-v1 |
| ベクトルDB | sqlite-vec |
| Confluence API | atlassian-python-api |
| CLI | typer |
| パッケージ管理 | uv |

## 環境変数

Confluence連携時に以下の環境変数を設定してください。

| 変数名 | 説明 |
|--------|------|
| `CONFLUENCE_URL` | Confluence APIのベースURL |
| `CONFLUENCE_TOKEN` | Confluence APIトークン |
| `CONFLUENCE_SPACE_KEY` | 取得するスペースキー |
