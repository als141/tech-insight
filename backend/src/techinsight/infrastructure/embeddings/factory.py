from __future__ import annotations

from techinsight.config.settings import Settings
from techinsight.infrastructure.embeddings.base import EmbeddingProvider
from techinsight.infrastructure.embeddings.qwen import QwenEmbeddingProvider


def build_embedding_provider(settings: Settings) -> EmbeddingProvider:
    active = settings.active_embedding_provider()
    if active == "qwen":
        return QwenEmbeddingProvider(settings)
    raise ValueError(f"Unsupported embedding provider: {active}")
