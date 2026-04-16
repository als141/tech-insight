from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class EmbeddingResult:
    provider: str
    model: str
    vectors: list[list[float]]


class EmbeddingProvider(ABC):
    provider_name: str
    model_name: str
    dimension: int

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> EmbeddingResult:
        raise NotImplementedError

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        raise NotImplementedError

    def prepare_corpus(self, texts: list[str]) -> EmbeddingResult:
        return self.embed_documents(texts)
