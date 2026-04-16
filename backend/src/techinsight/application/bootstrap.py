from __future__ import annotations

import csv
import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dateutil import parser
from sqlalchemy import text
from sqlalchemy.orm import Session

from techinsight.config.settings import Settings
from techinsight.domain.query import build_content_hash, format_document_text, stable_hash
from techinsight.infrastructure.embeddings.base import EmbeddingProvider
from techinsight.infrastructure.embeddings.helpers import read_jsonl, write_jsonl
from techinsight.infrastructure.models import Article, ArticleSearch, ImportJob


class BootstrapService:
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

    def run(self) -> dict:
        self._apply_migrations()
        return self._seed_articles()

    def _apply_migrations(self) -> None:
        self.session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                  version TEXT PRIMARY KEY,
                  applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
        )
        self.session.commit()
        applied = {
            row[0]
            for row in self.session.execute(text("SELECT version FROM schema_migrations")).all()
        }
        for path in sorted(self.settings.migrations_path.glob("*.sql")):
            if path.name in applied:
                continue
            for statement in self._split_sql(path.read_text(encoding="utf-8")):
                self.session.execute(text(statement))
            self.session.execute(
                text("INSERT INTO schema_migrations(version) VALUES (:version)"),
                {"version": path.name},
            )
            self.session.commit()

    def _seed_articles(self) -> dict:
        rows = self._load_csv_rows()
        csv_dataset_hash = stable_hash(json.dumps(rows, ensure_ascii=False, sort_keys=True))
        provider_name = self.embedding_provider.provider_name
        job = ImportJob(
            id=str(uuid.uuid4()),
            source_name=self.settings.csv_path.name,
            provider_name=provider_name,
            status="running",
            rows_total=len(rows),
        )
        self.session.add(job)
        self.session.commit()

        inserted = 0
        updated = 0
        skipped = 0
        articles: list[Article] = []
        for row in rows:
            content_hash = build_content_hash(row["title"], row["content"])
            existing = self.session.query(Article).filter(
                Article.source_type == "csv",
                Article.source_key == row["id"],
            ).one_or_none()
            published_at = self._parse_csv_datetime(row["published_at"])
            if existing is None:
                article = Article(
                    source_type="csv",
                    source_key=row["id"],
                    title=row["title"].strip(),
                    content=row["content"].strip(),
                    author=row["author"].strip(),
                    category=row["category"].strip(),
                    published_at=published_at,
                    content_hash=content_hash,
                    updated_at=datetime.now(timezone.utc),
                )
                self.session.add(article)
                inserted += 1
            else:
                if existing.content_hash == content_hash:
                    skipped += 1
                    article = existing
                else:
                    existing.title = row["title"].strip()
                    existing.content = row["content"].strip()
                    existing.author = row["author"].strip()
                    existing.category = row["category"].strip()
                    existing.published_at = published_at
                    existing.content_hash = content_hash
                    existing.updated_at = datetime.now(timezone.utc)
                    updated += 1
                    article = existing
            articles.append(article)
        self.session.commit()

        articles = list(
            self.session.query(Article)
            .filter(Article.deleted_at.is_(None))
            .order_by(Article.id.asc())
            .all()
        )
        embedding_dataset_hash = stable_hash(
            json.dumps(
                [
                    {
                        "id": article.source_key or str(article.id),
                        "source_key": article.source_key,
                        "title": article.title,
                        "content_hash": article.content_hash,
                        "author": article.author,
                        "category": article.category,
                        "published_at": article.published_at.isoformat(),
                    }
                    for article in articles
                ],
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        search_texts = [
            format_document_text(article.title, article.category, article.content)
            for article in articles
        ]
        vectors = self._load_or_create_vectors(
            articles=articles,
            search_texts=search_texts,
            dataset_hash=embedding_dataset_hash,
        )

        for article, search_text, vector in zip(articles, search_texts, vectors, strict=True):
            search_row = self.session.get(ArticleSearch, article.id)
            if search_row is None:
                search_row = ArticleSearch(article_id=article.id)
                self.session.add(search_row)
            search_row.search_text = search_text
            search_row.embedding = vector
            search_row.embedding_provider = self.embedding_provider.provider_name
            search_row.embedding_model = self.embedding_provider.model_name
            search_row.embedding_dim = len(vector)
            search_row.normalized = True
            search_row.indexed_at = datetime.now(timezone.utc)

        job.status = "completed"
        job.rows_inserted = inserted
        job.rows_updated = updated
        job.rows_skipped = skipped
        job.finished_at = datetime.now(timezone.utc)
        self.session.commit()
        return {
            "rows_total": len(rows),
            "rows_inserted": inserted,
            "rows_updated": updated,
            "rows_skipped": skipped,
            "provider": self.embedding_provider.provider_name,
            "dataset_hash": csv_dataset_hash,
            "embedding_dataset_hash": embedding_dataset_hash,
        }

    def _cache_paths(self) -> tuple[Path, Path]:
        if self.embedding_provider.provider_name == "qwen":
            return (
                self.settings.qwen_embedding_manifest_path,
                self.settings.qwen_embedding_cache_path,
            )
        raise ValueError(f"Unsupported embedding provider: {self.embedding_provider.provider_name}")

    def _load_or_create_vectors(
        self,
        *,
        articles: list[Article],
        search_texts: list[str],
        dataset_hash: str,
    ) -> list[list[float]]:
        self._restore_packaged_vectors()
        manifest_path, cache_path = self._cache_paths()
        if manifest_path.exists() and cache_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if (
                manifest.get("cache_version") == self.settings.embedding_cache_version
                and manifest.get("dataset_hash") == dataset_hash
                and manifest.get("dimension") == self.settings.embedding_dimension
                and manifest.get("count") == len(articles)
                and manifest.get("model") == self.embedding_provider.model_name
                and manifest.get("normalized") is True
            ):
                rows = read_jsonl(cache_path)
                lookup = {row["source_key"]: row["embedding"] for row in rows}
                if all(article.source_key in lookup for article in articles if article.source_key):
                    return [lookup[article.source_key or str(article.id)] for article in articles]

        unique_texts = list(dict.fromkeys(search_texts))
        result = self.embedding_provider.prepare_corpus(unique_texts)
        vectors_by_text = {
            text: vector for text, vector in zip(unique_texts, result.vectors, strict=True)
        }
        vectors = [vectors_by_text[text] for text in search_texts]

        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(
                {
                    "cache_version": self.settings.embedding_cache_version,
                    "provider": result.provider,
                    "model": result.model,
                    "dimension": self.settings.embedding_dimension,
                    "dataset_hash": dataset_hash,
                    "count": len(articles),
                    "normalized": True,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        write_jsonl(
            cache_path,
            [
                {
                    "article_id": article.id,
                    "source_key": article.source_key or str(article.id),
                    "content_hash": article.content_hash,
                    "embedding": vector,
                }
                for article, vector in zip(articles, vectors, strict=True)
            ],
        )
        return vectors

    def _restore_packaged_vectors(self) -> None:
        if self.embedding_provider.provider_name != "qwen":
            return

        packaged_dir = self.settings.packaged_vector_cache_dir
        files = {
            packaged_dir / "qwen-manifest.json": self.settings.qwen_embedding_manifest_path,
            packaged_dir / "qwen-embeddings.jsonl": self.settings.qwen_embedding_cache_path,
        }
        if not all(source.exists() for source in files):
            return
        if all(destination.exists() for destination in files.values()):
            return

        for source, destination in files.items():
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                shutil.copyfile(source, destination)

    def _load_csv_rows(self) -> list[dict[str, str]]:
        with self.settings.csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))

    def _parse_csv_datetime(self, value: str) -> datetime:
        parsed = parser.parse(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _split_sql(self, content: str) -> list[str]:
        return [chunk.strip() for chunk in content.split(";") if chunk.strip()]
