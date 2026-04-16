# Architecture

## 全体方針

TechInsight は、ローカルで再現しやすい構成を優先しました。  
外部サービスに強く依存させず、DB、API、フロントエンドを Docker Compose でまとめて起動します。

記事本体と検索用データを分け、CRUD と検索インデックス更新の責務を分離しています。

- Frontend: Next.js App Router
- Backend: FastAPI
- Database: PostgreSQL + pgvector
- Search: semantic / keyword / hybrid

## ディレクトリ

```text
backend/src/techinsight/
├── api/              # FastAPI router, schema
├── application/      # ArticleService, SearchService
├── config/           # settings
├── domain/           # query text, content hash
├── infrastructure/   # DB, embedding
└── tasks/            # bootstrap, vector packaging
```

フロントエンドは `frontend/src/app` を中心に置き、一覧画面、記事詳細ページ、API proxy、UI component を分けています。

## 検索

検索は 3 モードです。

- `keyword`: PostgreSQL full-text search と部分一致
- `semantic`: pgvector に保存した埋め込みベクトルで検索
- `hybrid`: keyword と semantic の候補を順位統合

セマンティック検索では、768 次元の正規化済みベクトルを `vector_ip_ops` で検索します。  
HNSW index は、1 万件程度まで増えた場合の検索速度を見据えて入れています。意味理解を無理やり補正するためのものではありません。

過剰なルールベース処理は入れていません。具体的には、検索語の勝手な言い換え、時間解釈、タイトル一致の固定加点は外しています。
重複記事は常に排除するのではなく、検索画面から含めるかどうかを切り替える扱いにしています。

## 埋め込み

通常起動では `Qwen/Qwen3-Embedding-0.6B` を使います。評価者が API キーを持っていなくても動かすためです。

- Qwen の出力を 768 次元に切り出し、L2 正規化して保存
- 記事ベクトルは `database/fixtures/vector-cache/` に同梱
- クエリベクトルは同じ Qwen model をローカルで実行して生成
- Qwen model 本体は Docker build 中に取得し、Git には含めない

初回起動時に実行用 cache がなければ、fixture から `database/vector-cache/` に復元します。

## 起動時の流れ

1. PostgreSQL 起動
2. backend 起動
3. migration 適用
4. CSV 取込
5. ベクトル生成または再利用
6. API 起動
7. frontend 起動
