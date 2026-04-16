# AGENTS

このリポジトリで作業するエージェントは、次の基準を守ること。

## 方針

- 提出物として自然に見える状態を保つ。途中実装、検証用の残骸、使っていない依存を残さない。
- 採用技術は FastAPI, Next.js, PostgreSQL, pgvector, Qwen local embedding を基準にする。
- Gemini, Supabase, MUI, reranker など、現在の設計にない依存や説明を戻さない。追加する場合は明確な理由と検証結果を残す。
- API キー、`.env`, DB 実体、model cache, Playwright の出力、`__pycache__` は提出物に含めない。
- README と docs には実装済みの機能だけを書く。将来構想は短く、現在動くものと混同しない。

## テスト要件

変更内容に応じて、該当するコマンドを実行する。

Backend を変更した場合:

```bash
cd backend
uv run ruff check src tests
uv run pytest
```

Frontend を変更した場合:

```bash
cd frontend
bun run lint
bun run build
```

API, CRUD, DB, bootstrap, Docker, 検索処理を変更した場合:

```bash
docker compose -f docker-compose.e2e.yml up --build --abort-on-container-exit --exit-code-from e2e
docker compose -f docker-compose.e2e.yml down -v
```

提出前に確認すること:

```bash
git status --short --branch --untracked-files=all
docker compose config
```

GitHub Actions の CI は pull request と `main` への push で、backend の lint/test、frontend の lint/build、Compose 定義検証を実行する。E2E は重いため自動 CI には入れず、提出前または DB/API に大きな変更があるときにローカルで実行する。

`docker compose up --build` だけで DB, backend, frontend が起動し、backend 起動時に migration と CSV 取込が走る状態を壊さない。

## データとベクトル

- `articles.csv` はヘッダ込み 1,001 行、記事 1,000 件を初期状態とする。
- 提出用ベクトルは `database/fixtures/vector-cache/` に置く。
- `qwen-manifest.json` の count は 1,000、dimension は 768、provider は `qwen` のままにする。
- `database/vector-cache/` は実行時 cache なので Git 管理しない。
- Qwen model 本体は Git に含めず、Docker build 中に取得する。

## UI/UX

- UI は日本語中心で、説明過多にしない。
- icon-only button には `aria-label` を付ける。
- フォームには label を付ける。
- 遅延があり得る検索、保存、削除には loading / disabled state を入れる。
- キーボード操作と focus state を壊さない。
- アクセシビリティは WCAG 2.2 AA を目標にする。
  https://www.w3.org/TR/WCAG22/
- UI レビュー時は Vercel Web Interface Guidelines も参照する。
  https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md

## レビュー観点

- 課題要件に対して必要十分か。
- ローカルで API キーなしに再現できるか。
- 1 万件程度に増えたときに明らかな設計破綻がないか。
- 過剰なルールベース補正で検索精度を見せかけていないか。
- 検索、CRUD、初期データ、ベクトル同梱の責務が分離されているか。
- チーム開発で読みやすい粒度に分割されているか。
