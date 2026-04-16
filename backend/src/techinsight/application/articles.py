from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from techinsight.domain.query import build_content_hash, format_document_text, normalize_query_text
from techinsight.infrastructure.embeddings.base import EmbeddingProvider
from techinsight.infrastructure.models import Article, ArticleSearch


class ArticleService:
    def __init__(self, session: Session, embedding_provider: EmbeddingProvider) -> None:
        self.session = session
        self.embedding_provider = embedding_provider

    def list_articles(
        self,
        *,
        page: int,
        page_size: int,
        keyword: str | None = None,
        categories: list[str] | None = None,
        authors: list[str] | None = None,
        sort: str = "published_desc",
    ) -> tuple[list[Article], int]:
        conditions = [Article.deleted_at.is_(None)]
        if keyword:
            like = f"%{normalize_query_text(keyword)}%"
            conditions.append(
                func.lower(
                    Article.title + " " + Article.content + " " + Article.category
                ).like(like)
            )
        if categories:
            conditions.append(Article.category.in_(categories))
        if authors:
            conditions.append(Article.author.in_(authors))

        statement = select(Article).where(and_(*conditions))
        if sort == "published_asc":
            statement = statement.order_by(Article.published_at.asc())
        elif sort == "title_asc":
            statement = statement.order_by(Article.title.asc())
        else:
            statement = statement.order_by(Article.published_at.desc())

        total = self.session.scalar(select(func.count()).select_from(statement.subquery())) or 0
        items = list(
            self.session.scalars(
                statement.offset((page - 1) * page_size).limit(page_size)
            ).all()
        )
        return items, total

    def get_article(self, article_id: int) -> Article | None:
        return self.session.get(Article, article_id)

    def get_related_variants(self, content_hash: str, article_id: int) -> list[Article]:
        statement = (
            select(Article)
            .where(
                Article.deleted_at.is_(None),
                Article.content_hash == content_hash,
                Article.id != article_id,
            )
            .order_by(Article.published_at.desc())
        )
        return list(self.session.scalars(statement).all())

    def get_related_by_embedding(self, article_id: int, limit: int = 5) -> list[Article]:
        search_doc = self.session.get(ArticleSearch, article_id)
        if not search_doc:
            return []
        statement = (
            select(Article)
            .join(ArticleSearch, ArticleSearch.article_id == Article.id)
            .where(Article.deleted_at.is_(None), Article.id != article_id)
            .order_by(ArticleSearch.embedding.max_inner_product(search_doc.embedding))
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())

    def create_article(
        self,
        *,
        title: str,
        content: str,
        author: str,
        category: str,
        published_at: datetime,
    ) -> Article:
        article = Article(
            source_type="manual",
            source_key=None,
            title=title.strip(),
            content=content.strip(),
            author=author.strip(),
            category=category.strip(),
            published_at=published_at.astimezone(timezone.utc),
            content_hash=build_content_hash(title, content),
            updated_at=datetime.now(timezone.utc),
        )
        self.session.add(article)
        self.session.flush()
        self._upsert_search_document(article)
        self.session.commit()
        self.session.refresh(article)
        return article

    def update_article(
        self,
        article: Article,
        *,
        title: str,
        content: str,
        author: str,
        category: str,
        published_at: datetime,
    ) -> Article:
        article.title = title.strip()
        article.content = content.strip()
        article.author = author.strip()
        article.category = category.strip()
        article.published_at = published_at.astimezone(timezone.utc)
        article.content_hash = build_content_hash(title, content)
        article.updated_at = datetime.now(timezone.utc)
        self._upsert_search_document(article)
        self.session.commit()
        self.session.refresh(article)
        return article

    def delete_article(self, article: Article) -> None:
        article.deleted_at = datetime.now(timezone.utc)
        article.updated_at = datetime.now(timezone.utc)
        self.session.commit()

    def get_filters(self) -> dict[str, list[str]]:
        categories = list(
            self.session.scalars(
                select(Article.category)
                .where(Article.deleted_at.is_(None))
                .distinct()
                .order_by(Article.category.asc())
            ).all()
        )
        authors = list(
            self.session.scalars(
                select(Article.author)
                .where(Article.deleted_at.is_(None))
                .distinct()
                .order_by(Article.author.asc())
            ).all()
        )
        return {"categories": categories, "authors": authors}

    def _upsert_search_document(self, article: Article) -> None:
        search_text = format_document_text(article.title, article.category, article.content)
        embedding = self.embedding_provider.embed_documents([search_text])
        search_row = self.session.get(ArticleSearch, article.id)
        if search_row is None:
            search_row = ArticleSearch(article_id=article.id)
            self.session.add(search_row)
        search_row.search_text = search_text
        search_row.embedding = embedding.vectors[0]
        search_row.embedding_provider = embedding.provider
        search_row.embedding_model = embedding.model
        search_row.embedding_dim = len(embedding.vectors[0])
        search_row.normalized = True
        search_row.indexed_at = datetime.now(timezone.utc)
