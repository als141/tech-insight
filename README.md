# TechInsight

技術記事 CSV を読み込んで、記事管理と検索を行うローカル完結の Web アプリです。  
評価者が API キーを持っていない前提なので、通常起動では `Qwen/Qwen3-Embedding-0.6B` をローカル埋め込みとして使います。

## 起動

```bash
docker compose up --build
```

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000/api/v1`
- OpenAPI: `http://localhost:8000/docs`

`.env` を作らなくても、API キーなしで動く既定値を `docker-compose.yml` に入れています。
ポートや DB 接続情報を変えたい場合だけ、`.env.example` を参考に `.env` を作成してください。
Qwen の model 本体は Docker build 中に取得されます。サイズは約 1.2GB あるため、初回 build は少し時間がかかります。

## できること

- 記事の一覧、詳細、作成、編集、削除
- キーワード検索、セマンティック検索、ハイブリッド検索
- カテゴリ、著者での絞り込み
- 記事詳細ページへの動的ルート遷移
- CSV 取込とベクトル生成の自動実行

## 技術構成

- Backend: FastAPI, SQLAlchemy, uv
- Frontend: Next.js App Router, TypeScript, shadcn/ui, Tailwind CSS, bun
- Database: PostgreSQL, pgvector
- Embedding:
  - `Qwen/Qwen3-Embedding-0.6B`
  - 768 次元に切り出して L2 正規化
- Search:
  - semantic: pgvector
  - keyword: PostgreSQL full-text search + partial match
  - hybrid: semantic と keyword の順位統合

## 検索について

セマンティック検索は `article_search.embedding` に保存した 768 次元ベクトルを使います。  
ベクトルは正規化して保存し、pgvector の HNSW index と `vector_ip_ops` で検索します。

HNSW は精度を無理に上げるためではなく、件数が 1 万件程度に増えた場合でも近傍探索を軽くするために入れています。1,000 件なら exact search でも十分ですが、課題文で増加時の効率も求められているため採用しました。

## ベクトルの扱い

提出時は API キーなしで動く必要があるため、Qwen provider を既定にしています。  
再生成する場合は次のコマンドを使います。

```bash
docker compose exec backend uv run techinsight-package-vectors
```

実行時のキャッシュは `database/vector-cache/` に保存されます。このディレクトリは Docker build context から除外しています。  
提出用には `database/fixtures/vector-cache/` に Qwen で生成した記事ベクトルを同梱し、初回起動時に `database/vector-cache/` へ復元するようにしています。
Qwen model 本体は通常の Git 管理には入れず、Docker build の中で取得します。

## 開発コマンド

Backend:

```bash
cd backend
uv sync
uv run ruff check src tests
uv run pytest
```

Frontend:

```bash
cd frontend
bun install
bun run lint
bun run build
```

Docker 内だけで CRUD の E2E を確認する場合:

```bash
docker compose -f docker-compose.e2e.yml up --build --abort-on-container-exit --exit-code-from e2e
docker compose -f docker-compose.e2e.yml down -v
```

この E2E は専用の Docker volume を使うため、通常開発用の `database/postgres-data/` は触りません。

## CI

Pull request と `main` への push では、GitHub Actions で backend の lint/test、frontend の lint/build、Compose 定義の検証を実行します。Docker E2E は Qwen model の取得を含み重いため、自動 CI には含めず、提出前や大きな変更時にローカルで実行します。

## ドキュメント

- [Architecture](./docs/architecture.md)
- [API](./docs/api.md)
- [DB](./docs/db.md)

## 実装上のメモ

- UI は一覧、検索、作成、編集、削除を同じ画面で扱えるようにし、記事詳細は URL を持つページとして分けています。
- 検索画面では、キーワード、セマンティック、ハイブリッドを切り替えられます。重複記事もスイッチで「含める / 含めない」を選べます。
- DB は外部の BaaS に寄せず、PostgreSQL + pgvector にまとめています。記事本体は `articles`、検索用データは `article_search` に分け、検索データを作り直しやすい形にしています。
- ベクトルは 768 次元に揃えて正規化し、HNSW index で検索します。1,000 件だけでなく、件数が増えた場合の検索効率も考慮しています。
- 検索語の勝手な言い換え、時間解釈、タイトル一致の固定加点は入れていません。検索精度を無理に盛るより、挙動を説明しやすい実装にしています。
- backend、frontend、database、docs を分け、API と DB の設計は `docs/` に置いています。チームで触る場合も、見る場所が分かれすぎない構成にしています。
- `docker compose up --build` だけで起動できるようにし、提出用のベクトルは `database/fixtures/vector-cache/` に同梱しています。API キーなしでも同じ初期データで確認できます。
