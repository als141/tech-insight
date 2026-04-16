from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ArticleBase(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    content: str = Field(min_length=20)
    author: str = Field(min_length=2, max_length=128)
    category: str = Field(min_length=2, max_length=64)
    published_at: datetime


class ArticleCreate(ArticleBase):
    pass


class ArticleUpdate(ArticleBase):
    pass


class ArticleVariant(BaseModel):
    id: int
    title: str
    author: str
    category: str
    published_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArticleSummary(BaseModel):
    id: int
    title: str
    content: str
    author: str
    category: str
    published_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArticleDetail(ArticleSummary):
    duplicate_count: int
    variants: list[ArticleVariant]
    related_articles: list[ArticleVariant]


class ArticleListResponse(BaseModel):
    items: list[ArticleSummary]
    total: int
    page: int
    page_size: int


class SearchFilters(BaseModel):
    category: list[str] = Field(default_factory=list)
    author: list[str] = Field(default_factory=list)
    publishedFrom: datetime | None = None
    publishedTo: datetime | None = None


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    mode: str = Field(default="hybrid", pattern="^(keyword|semantic|hybrid)$")
    filters: SearchFilters = Field(default_factory=SearchFilters)
    sort: str = Field(default="relevance", pattern="^(relevance|newest|oldest)$")
    includeDuplicates: bool = True
    page: int = Field(default=1, ge=1)
    pageSize: int = Field(default=20, ge=1, le=50)


class SearchItem(BaseModel):
    articleId: int
    title: str
    author: str
    category: str
    contentPreview: str
    publishedAt: datetime
    semanticScore: float
    keywordScore: float
    finalScore: float
    duplicateCount: int
    matchedBy: list[str]


class SearchResponse(BaseModel):
    items: list[SearchItem]
    total: int


class FilterMetaResponse(BaseModel):
    categories: list[str]
    authors: list[str]


class HealthResponse(BaseModel):
    status: str
    database: str
    embeddingProvider: str
    embeddingModel: str
