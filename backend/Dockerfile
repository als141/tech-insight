FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

COPY database /app/database
COPY articles.csv /app/articles.csv
COPY .env.example /app/.env.example

WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock /app/backend/
RUN uv sync --frozen --no-dev --no-install-project
RUN .venv/bin/python - <<'PY'
from sentence_transformers import SentenceTransformer

model = SentenceTransformer(
    "Qwen/Qwen3-Embedding-0.6B",
    cache_folder="/app/database/model-cache",
    truncate_dim=768,
    device="cpu",
)
model.max_seq_length = 512
PY

COPY backend /app/backend
RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["sh", "-c", ".venv/bin/python -m techinsight.tasks.bootstrap && .venv/bin/uvicorn techinsight.main:app --host 0.0.0.0 --port 8000"]
