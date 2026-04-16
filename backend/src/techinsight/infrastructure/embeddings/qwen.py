from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer

from techinsight.config.settings import Settings
from techinsight.infrastructure.embeddings.base import EmbeddingProvider, EmbeddingResult
from techinsight.infrastructure.embeddings.helpers import l2_normalize, l2_normalize_vector


class QwenEmbeddingProvider(EmbeddingProvider):
    provider_name = "qwen"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.model_name = settings.qwen_model
        self.dimension = settings.embedding_dimension
        self._model: SentenceTransformer | None = None

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(
                self.model_name,
                cache_folder=str(self.settings.embedding_model_cache_dir),
                truncate_dim=self.dimension,
                device=self.settings.qwen_device,
            )
            self._model.max_seq_length = self.settings.qwen_max_seq_length
        return self._model

    def embed_documents(self, texts: list[str]) -> EmbeddingResult:
        if not texts:
            return EmbeddingResult(provider=self.provider_name, model=self.model_name, vectors=[])
        vectors = self._encode(texts, prompt_name=None)
        return EmbeddingResult(
            provider=self.provider_name,
            model=self.model_name,
            vectors=vectors.astype(float).tolist(),
        )

    def embed_query(self, text: str) -> list[float]:
        vector = self._encode([text], prompt_name="query")[0]
        return l2_normalize_vector(vector).astype(float).tolist()

    def _encode(self, texts: list[str], *, prompt_name: str | None) -> np.ndarray:
        model = self._get_model()
        kwargs = {
            "batch_size": self.settings.embedding_batch_size,
            "convert_to_numpy": True,
            "normalize_embeddings": False,
            "show_progress_bar": False,
        }
        if prompt_name is not None:
            kwargs["prompt_name"] = prompt_name
        vectors = model.encode(texts, **kwargs)
        return l2_normalize(np.asarray(vectors, dtype=np.float32))
