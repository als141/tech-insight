# DB Design

## 概要

検索用メタデータと本体データを分離し、記事 CRUD とベクトル検索を両立しています。

## テーブル

### `articles`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `bigserial` | PK |
| `source_type` | `text` | `csv` / `manual` |
| `source_key` | `text` | CSV の元 ID |
| `title` | `text` | 記事タイトル |
| `content` | `text` | 本文 |
| `author` | `text` | 著者 |
| `category` | `text` | カテゴリ |
| `published_at` | `timestamptz` | 公開日時 |
| `content_hash` | `char(64)` | 重複判定 |
| `created_at` | `timestamptz` | 作成日時 |
| `updated_at` | `timestamptz` | 更新日時 |
| `deleted_at` | `timestamptz` | 論理削除 |

### `article_search`

| Column | Type | Notes |
| --- | --- | --- |
| `article_id` | `bigint` | PK / FK |
| `search_text` | `text` | embedding / lexical 用文面 |
| `search_tsv` | `tsvector` | `search_text` から生成される永続 lexical 列 |
| `embedding` | `vector(768)` | pgvector |
| `embedding_provider` | `text` | `qwen` |
| `embedding_model` | `text` | モデル名 |
| `embedding_dim` | `int` | 次元数 |
| `normalized` | `boolean` | 正規化済みフラグ |
| `indexed_at` | `timestamptz` | インデックス更新日時 |

### `import_jobs`

CSV 取込や再ベクトル化のジョブ記録。

## インデックス

- `uq_articles_source_key`
- `idx_articles_category`
- `idx_articles_author`
- `idx_articles_published_at`
- `idx_articles_content_hash`
- `idx_article_search_tsv`
- `idx_article_search_embedding_hnsw`

## 設計意図

- `content_hash` で同一内容の別版を束ねる
- `article_search` を分離して検索再生成を容易にする
- HNSW で 10,000 件規模までの近似検索を見据える
- ベクトルは L2 正規化し、`vector_ip_ops` で inner product 検索に寄せる
- lexical 側は `search_tsv` を永続列として保持し、hybrid search の安定性を上げる
