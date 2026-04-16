from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(PROJECT_ROOT / ".env", override=False)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    app_name: str = "TechInsight API"
    api_prefix: str = "/api/v1"
    allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    postgres_db: str = "techinsight"
    postgres_user: str = "techinsight"
    postgres_password: str = "techinsight"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    embedding_provider: str = "qwen"
    embedding_dimension: int = 768
    embedding_batch_size: int = 8
    embedding_cache_version: str = "v2-normalized-ip"
    embedding_model_cache_dir: Path = PROJECT_ROOT / "database" / "model-cache"
    qwen_model: str = "Qwen/Qwen3-Embedding-0.6B"
    qwen_device: str = "cpu"
    qwen_max_seq_length: int = 512
    csv_path: Path = PROJECT_ROOT / "articles.csv"
    migrations_path: Path = PROJECT_ROOT / "database" / "migrations"
    vector_cache_dir: Path = PROJECT_ROOT / "database" / "vector-cache"
    packaged_vector_cache_dir: Path = PROJECT_ROOT / "database" / "fixtures" / "vector-cache"
    qwen_embedding_manifest_path: Path = (
        PROJECT_ROOT / "database" / "vector-cache" / "qwen-manifest.json"
    )
    qwen_embedding_cache_path: Path = (
        PROJECT_ROOT / "database" / "vector-cache" / "qwen-embeddings.jsonl"
    )
    search_default_mode: str = "hybrid"
    search_rrf_k: int = 60
    semantic_candidate_limit: int = 80
    lexical_candidate_limit: int = 50
    lexical_partial_limit: int = 50
    lexical_partial_min_similarity: float = 0.12
    semantic_ef_search: int = 120

    def database_url(self) -> str:
        return (
            "postgresql+psycopg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    def active_embedding_provider(self) -> str:
        if self.embedding_provider == "auto":
            return "qwen"
        return self.embedding_provider


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
