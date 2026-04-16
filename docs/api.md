# API Design

## Base URL

`/api/v1`

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/health` | DB と埋め込み設定の疎通確認 |
| GET | `/articles` | 記事一覧 |
| GET | `/articles/{id}` | 記事詳細 |
| POST | `/articles` | 記事作成 |
| PUT | `/articles/{id}` | 記事更新 |
| DELETE | `/articles/{id}` | 記事削除 |
| POST | `/search` | ハイブリッド検索 |
| GET | `/meta/filters` | フィルタ候補 |
| POST | `/admin/reindex` | 再取込と再ベクトル化 |

## `POST /search`

### Request

```json
{
  "query": "PostgreSQL optimization",
  "mode": "hybrid",
  "filters": {
    "category": ["Backend"],
    "author": [],
    "publishedFrom": null,
    "publishedTo": null
  },
  "sort": "relevance",
  "includeDuplicates": true,
  "page": 1,
  "pageSize": 20
}
```

### Response

```json
{
  "items": [
    {
      "articleId": 1,
      "title": "Implementing PostgreSQL: Database schema design and query optimization",
      "author": "Ito",
      "category": "Backend",
      "contentPreview": "...",
      "publishedAt": "2025-09-19T22:00:00Z",
      "semanticScore": 0.709,
      "keywordScore": 0.000,
      "finalScore": 0.075,
      "duplicateCount": 4,
      "matchedBy": ["semantic", "keyword"]
    }
  ],
  "total": 5
}
```

## `GET /articles`

### Query Parameters

- `page`
- `page_size`
- `keyword`
- `category`
- `author`
- `sort`

## `GET /articles/{id}`

### Response

- 本文全文
- 別版一覧
- 類似記事一覧

## `POST /admin/reindex`

CSV 再取込、差分反映、ベクトル再生成を同期的に実行します。開発用の管理エンドポイントです。

## スコアリング方針

- semantic rank と keyword rank を RRF で統合
