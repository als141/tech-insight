from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from techinsight.api.deps import (
    get_app_settings,
    get_article_service,
    get_embedding_provider,
    get_search_service,
)
from techinsight.api.schemas import (
    ArticleCreate,
    ArticleDetail,
    ArticleListResponse,
    ArticleSummary,
    ArticleUpdate,
    FilterMetaResponse,
    HealthResponse,
    SearchRequest,
    SearchResponse,
)
from techinsight.application.bootstrap import BootstrapService
from techinsight.config.settings import Settings
from techinsight.infrastructure.db import get_db
from techinsight.infrastructure.embeddings.base import EmbeddingProvider

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
    provider: EmbeddingProvider = Depends(get_embedding_provider),
) -> HealthResponse:
    session.execute(text("SELECT 1"))
    return HealthResponse(
        status="ok",
        database="ok",
        embeddingProvider=settings.active_embedding_provider(),
        embeddingModel=provider.model_name,
    )


@router.get("/articles", response_model=ArticleListResponse)
def list_articles(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    keyword: str | None = None,
    category: list[str] | None = Query(default=None),
    author: list[str] | None = Query(default=None),
    sort: str = Query(default="published_desc"),
    session: Session = Depends(get_db),
) -> ArticleListResponse:
    service = get_article_service(session)
    items, total = service.list_articles(
        page=page,
        page_size=page_size,
        keyword=keyword,
        categories=category,
        authors=author,
        sort=sort,
    )
    return ArticleListResponse(
        items=[ArticleSummary.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/articles/{article_id}", response_model=ArticleDetail)
def get_article(article_id: int, session: Session = Depends(get_db)) -> ArticleDetail:
    service = get_article_service(session)
    article = service.get_article(article_id)
    if article is None or article.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Article not found")
    variants = service.get_related_variants(article.content_hash, article.id)
    related = service.get_related_by_embedding(article.id, limit=5)
    payload = ArticleDetail(
        **ArticleSummary.model_validate(article).model_dump(),
        duplicate_count=len(variants),
        variants=variants,
        related_articles=related,
    )
    return payload


@router.post("/articles", response_model=ArticleSummary, status_code=201)
def create_article(payload: ArticleCreate, session: Session = Depends(get_db)) -> ArticleSummary:
    service = get_article_service(session)
    article = service.create_article(**payload.model_dump())
    return ArticleSummary.model_validate(article)


@router.put("/articles/{article_id}", response_model=ArticleSummary)
def update_article(
    article_id: int,
    payload: ArticleUpdate,
    session: Session = Depends(get_db),
) -> ArticleSummary:
    service = get_article_service(session)
    article = service.get_article(article_id)
    if article is None or article.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Article not found")
    article = service.update_article(article, **payload.model_dump())
    return ArticleSummary.model_validate(article)


@router.delete("/articles/{article_id}", status_code=204)
def delete_article(article_id: int, session: Session = Depends(get_db)) -> None:
    service = get_article_service(session)
    article = service.get_article(article_id)
    if article is None or article.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Article not found")
    service.delete_article(article)
    return None


@router.post("/search", response_model=SearchResponse)
def search_articles(payload: SearchRequest, session: Session = Depends(get_db)) -> SearchResponse:
    service = get_search_service(session)
    results = service.search(
        query=payload.query,
        mode=payload.mode,
        categories=payload.filters.category,
        authors=payload.filters.author,
        published_from=payload.filters.publishedFrom,
        published_to=payload.filters.publishedTo,
        page=payload.page,
        page_size=payload.pageSize,
        sort=payload.sort,
        include_duplicates=payload.includeDuplicates,
    )
    return SearchResponse.model_validate(results)


@router.get("/meta/filters", response_model=FilterMetaResponse)
def get_filters(session: Session = Depends(get_db)) -> FilterMetaResponse:
    service = get_article_service(session)
    return FilterMetaResponse.model_validate(service.get_filters())


@router.post("/admin/reindex")
def reindex_articles(
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
    provider: EmbeddingProvider = Depends(get_embedding_provider),
) -> dict:
    service = BootstrapService(session=session, settings=settings, embedding_provider=provider)
    return service.run()
