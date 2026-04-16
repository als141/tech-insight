from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import and_, func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from techinsight.config.settings import Settings
from techinsight.domain.query import (
    format_query_text,
    normalize_query_text,
)
from techinsight.infrastructure.embeddings.base import EmbeddingProvider
from techinsight.infrastructure.models import Article, ArticleSearch


class SearchService:
    def __init__(
        self,
        *,
        session: Session,
        settings: Settings,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.session = session
        self.settings = settings
        self.embedding_provider = embedding_provider

    def search(
        self,
        *,
        query: str,
        mode: str,
        categories: list[str] | None,
        authors: list[str] | None,
        published_from: datetime | None,
        published_to: datetime | None,
        page: int,
        page_size: int,
        sort: str,
        include_duplicates: bool = True,
    ) -> dict:
        normalized_query = normalize_query_text(query)
        query_vector = None
        if mode in {"semantic", "hybrid"}:
            query_vector = self.embedding_provider.embed_query(format_query_text(query))

        semantic_items = (
            self._semantic_candidates(
                query_vector=query_vector,
                categories=categories,
                authors=authors,
                published_from=published_from,
                published_to=published_to,
                limit=self.settings.semantic_candidate_limit,
            )
            if query_vector is not None
            else []
        )
        lexical_items = (
            self._merge_lexical_candidates(
                query=normalized_query,
                categories=categories,
                authors=authors,
                published_from=published_from,
                published_to=published_to,
                limit=self.settings.lexical_candidate_limit,
            )
            if mode in {"keyword", "hybrid"}
            else []
        )
        merged = self._merge_results(
            semantic_items=semantic_items,
            lexical_items=lexical_items,
        )

        if sort == "newest":
            merged.sort(key=lambda item: item["publishedAt"], reverse=True)
        elif sort == "oldest":
            merged.sort(key=lambda item: item["publishedAt"])
        else:
            merged.sort(key=lambda item: item["finalScore"], reverse=True)

        if not include_duplicates:
            merged = self._remove_duplicate_content(merged)

        total = len(merged)
        start = (page - 1) * page_size
        end = start + page_size
        return {
            "items": merged[start:end],
            "total": total,
        }

    def _base_conditions(
        self,
        *,
        categories: list[str] | None,
        authors: list[str] | None,
        published_from: datetime | None,
        published_to: datetime | None,
    ) -> list:
        conditions = [Article.deleted_at.is_(None)]
        if categories:
            conditions.append(Article.category.in_(categories))
        if authors:
            conditions.append(Article.author.in_(authors))
        if published_from:
            conditions.append(Article.published_at >= published_from.astimezone(timezone.utc))
        if published_to:
            conditions.append(Article.published_at < published_to.astimezone(timezone.utc))
        return conditions

    def _semantic_candidates(
        self,
        *,
        query_vector: list[float],
        categories: list[str] | None,
        authors: list[str] | None,
        published_from: datetime | None,
        published_to: datetime | None,
        limit: int,
    ) -> list[dict]:
        self._configure_semantic_search_session()
        statement = (
            select(
                Article.id,
                Article.title,
                Article.author,
                Article.category,
                Article.content,
                Article.content_hash,
                Article.published_at,
                (-ArticleSearch.embedding.max_inner_product(query_vector)).label("semantic_score"),
            )
            .join(ArticleSearch, ArticleSearch.article_id == Article.id)
            .where(
                and_(
                    *self._base_conditions(
                        categories=categories,
                        authors=authors,
                        published_from=published_from,
                        published_to=published_to,
                    )
                )
            )
            .order_by(ArticleSearch.embedding.max_inner_product(query_vector))
            .limit(limit)
        )
        rows = self.session.execute(statement).all()
        return [
            self._row_to_dict(row, semantic_score=float(row.semantic_score or 0.0))
            for row in rows
        ]

    def _lexical_candidates(
        self,
        *,
        query: str,
        categories: list[str] | None,
        authors: list[str] | None,
        published_from: datetime | None,
        published_to: datetime | None,
        limit: int,
    ) -> list[dict]:
        statement = (
            select(
                Article.id,
                Article.title,
                Article.author,
                Article.category,
                Article.content,
                Article.content_hash,
                Article.published_at,
                func.ts_rank_cd(
                    ArticleSearch.search_tsv,
                    func.plainto_tsquery("simple", query),
                ).label("keyword_score"),
            )
            .join(ArticleSearch, ArticleSearch.article_id == Article.id)
            .where(
                and_(
                    *self._base_conditions(
                        categories=categories,
                        authors=authors,
                        published_from=published_from,
                        published_to=published_to,
                    ),
                    ArticleSearch.search_tsv.op("@@")(func.plainto_tsquery("simple", query)),
                )
            )
            .order_by(
                func.ts_rank_cd(
                    ArticleSearch.search_tsv,
                    func.plainto_tsquery("simple", query),
                ).desc()
            )
            .limit(limit)
        )
        rows = self.session.execute(statement).all()
        return [
            self._row_to_dict(row, keyword_score=float(row.keyword_score or 0.0))
            for row in rows
        ]

    def _partial_lexical_candidates(
        self,
        *,
        query: str,
        categories: list[str] | None,
        authors: list[str] | None,
        published_from: datetime | None,
        published_to: datetime | None,
        limit: int,
    ) -> list[dict]:
        like = f"%{query}%"
        title_similarity = func.similarity(func.lower(Article.title), query)
        content_similarity = func.similarity(func.lower(Article.content), query)
        category_similarity = func.similarity(func.lower(Article.category), query)
        best_similarity = func.greatest(title_similarity, content_similarity, category_similarity)

        statement = (
            select(
                Article.id,
                Article.title,
                Article.author,
                Article.category,
                Article.content,
                Article.content_hash,
                Article.published_at,
                best_similarity.label("keyword_score"),
            )
            .join(ArticleSearch, ArticleSearch.article_id == Article.id)
            .where(
                and_(
                    *self._base_conditions(
                        categories=categories,
                        authors=authors,
                        published_from=published_from,
                        published_to=published_to,
                    ),
                    func.lower(ArticleSearch.search_text).like(like),
                    best_similarity >= self.settings.lexical_partial_min_similarity,
                )
            )
            .order_by(best_similarity.desc(), Article.published_at.desc())
            .limit(limit)
        )
        rows = self.session.execute(statement).all()
        return [
            self._row_to_dict(row, keyword_score=float(row.keyword_score or 0.0))
            for row in rows
        ]

    def _merge_lexical_candidates(
        self,
        *,
        query: str,
        categories: list[str] | None,
        authors: list[str] | None,
        published_from: datetime | None,
        published_to: datetime | None,
        limit: int,
    ) -> list[dict]:
        full_text_items = self._lexical_candidates(
            query=query,
            categories=categories,
            authors=authors,
            published_from=published_from,
            published_to=published_to,
            limit=limit,
        )
        partial_items = self._partial_lexical_candidates(
            query=query,
            categories=categories,
            authors=authors,
            published_from=published_from,
            published_to=published_to,
            limit=self.settings.lexical_partial_limit,
        )

        merged: dict[int, dict] = {}
        for item in full_text_items:
            merged[item["articleId"]] = item
        for item in partial_items:
            existing = merged.get(item["articleId"])
            if existing is None or item["keywordScore"] > existing["keywordScore"]:
                merged[item["articleId"]] = item

        return sorted(merged.values(), key=lambda row: row["keywordScore"], reverse=True)[:limit]

    def _merge_results(
        self,
        *,
        semantic_items: list[dict],
        lexical_items: list[dict],
    ) -> list[dict]:
        merged: dict[int, dict] = {}
        for rank, item in enumerate(semantic_items, start=1):
            merged[item["articleId"]] = {
                **item,
                "semanticScore": item.get("semanticScore", 0.0),
                "keywordScore": 0.0,
                "finalScore": 1 / (self.settings.search_rrf_k + rank),
                "matchedBy": ["semantic"],
            }
        for rank, item in enumerate(lexical_items, start=1):
            existing = merged.get(item["articleId"])
            lexical_score = item.get("keywordScore", 0.0)
            if existing:
                existing["keywordScore"] = lexical_score
                existing["finalScore"] += 1 / (self.settings.search_rrf_k + rank)
                if "keyword" not in existing["matchedBy"]:
                    existing["matchedBy"].append("keyword")
            else:
                merged[item["articleId"]] = {
                    **item,
                    "semanticScore": 0.0,
                    "keywordScore": lexical_score,
                    "finalScore": 1 / (self.settings.search_rrf_k + rank),
                    "matchedBy": ["keyword"],
                }

        return sorted(merged.values(), key=lambda row: row["finalScore"], reverse=True)

    def _remove_duplicate_content(self, items: list[dict]) -> list[dict]:
        seen: set[str] = set()
        unique_items: list[dict] = []
        for item in items:
            content_hash = item["contentHash"]
            if content_hash in seen:
                continue
            seen.add(content_hash)
            unique_items.append(item)
        return unique_items

    def _row_to_dict(self, row, *, semantic_score: float = 0.0, keyword_score: float = 0.0) -> dict:
        variants = self._variant_count(row.content_hash)
        return {
            "articleId": row.id,
            "title": row.title,
            "author": row.author,
            "category": row.category,
            "contentPreview": row.content[:220],
            "publishedAt": row.published_at,
            "semanticScore": semantic_score,
            "keywordScore": keyword_score,
            "duplicateCount": variants - 1 if variants > 0 else 0,
            "contentHash": row.content_hash,
        }

    def _variant_count(self, content_hash: str) -> int:
        statement = select(func.count()).select_from(Article).where(
            Article.deleted_at.is_(None), Article.content_hash == content_hash
        )
        return int(self.session.scalar(statement) or 0)

    def _configure_semantic_search_session(self) -> None:
        try:
            self.session.execute(
                text(f"SET LOCAL hnsw.ef_search = {self.settings.semantic_ef_search}")
            )
            self.session.execute(text("SET LOCAL hnsw.iterative_scan = strict_order"))
        except SQLAlchemyError:
            self.session.rollback()
