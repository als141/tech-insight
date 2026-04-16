from __future__ import annotations

import csv
import json
import shutil
from datetime import timezone

from dateutil import parser

from techinsight.config.settings import get_settings
from techinsight.domain.query import build_content_hash, format_document_text, stable_hash
from techinsight.infrastructure.embeddings.helpers import write_jsonl
from techinsight.infrastructure.embeddings.qwen import QwenEmbeddingProvider


def main() -> None:
    settings = get_settings().model_copy(update={"embedding_provider": "qwen"})
    provider = QwenEmbeddingProvider(settings)
    rows = _load_csv_rows(settings.csv_path)
    articles = []
    for row in rows:
        published_at = _parse_csv_datetime(row["published_at"])
        articles.append(
            {
                "id": row["id"],
                "source_key": row["id"],
                "title": row["title"].strip(),
                "content": row["content"].strip(),
                "author": row["author"].strip(),
                "category": row["category"].strip(),
                "published_at": published_at.isoformat(),
                "content_hash": build_content_hash(row["title"], row["content"]),
            }
        )

    dataset_hash = stable_hash(
        json.dumps(
            [
                {
                    "id": article["id"],
                    "source_key": article["source_key"],
                    "title": article["title"],
                    "content_hash": article["content_hash"],
                    "author": article["author"],
                    "category": article["category"],
                    "published_at": article["published_at"],
                }
                for article in articles
            ],
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    search_texts = [
        format_document_text(article["title"], article["category"], article["content"])
        for article in articles
    ]
    unique_texts = list(dict.fromkeys(search_texts))
    result = provider.embed_documents(unique_texts)
    vectors_by_text = {
        text: vector for text, vector in zip(unique_texts, result.vectors, strict=True)
    }
    vectors = [vectors_by_text[text] for text in search_texts]

    settings.qwen_embedding_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    settings.qwen_embedding_manifest_path.write_text(
        json.dumps(
            {
                "cache_version": settings.embedding_cache_version,
                "provider": result.provider,
                "model": result.model,
                "dimension": settings.embedding_dimension,
                "dataset_hash": dataset_hash,
                "count": len(articles),
                "unique_count": len(unique_texts),
                "normalized": True,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    write_jsonl(
        settings.qwen_embedding_cache_path,
        [
            {
                "article_id": article["id"],
                "source_key": article["source_key"],
                "content_hash": article["content_hash"],
                "embedding": vector,
            }
            for article, vector in zip(articles, vectors, strict=True)
        ],
    )
    _copy_qwen_vectors_to_package(settings)
    print(
        json.dumps(
            {
                "provider": result.provider,
                "model": result.model,
                "dimension": settings.embedding_dimension,
                "count": len(articles),
                "dataset_hash": dataset_hash,
            },
            ensure_ascii=False,
        )
    )


def _load_csv_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _parse_csv_datetime(value: str):
    parsed = parser.parse(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _copy_qwen_vectors_to_package(settings) -> None:
    packaged_dir = settings.packaged_vector_cache_dir
    packaged_dir.mkdir(parents=True, exist_ok=True)
    for source in (
        settings.qwen_embedding_manifest_path,
        settings.qwen_embedding_cache_path,
    ):
        shutil.copyfile(source, packaged_dir / source.name)


if __name__ == "__main__":
    main()
