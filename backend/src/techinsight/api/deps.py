from __future__ import annotations

from functools import lru_cache

from sqlalchemy.orm import Session

from techinsight.application.articles import ArticleService
from techinsight.application.search import SearchService
from techinsight.config.settings import Settings, get_settings
from techinsight.infrastructure.embeddings.base import EmbeddingProvider
from techinsight.infrastructure.embeddings.factory import build_embedding_provider


@lru_cache(maxsize=1)
def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    return build_embedding_provider(settings)


def get_article_service(session: Session) -> ArticleService:
    return ArticleService(session=session, embedding_provider=get_embedding_provider())


def get_search_service(session: Session) -> SearchService:
    settings = get_settings()
    return SearchService(
        session=session,
        settings=settings,
        embedding_provider=get_embedding_provider(),
    )


def get_app_settings() -> Settings:
    return get_settings()
