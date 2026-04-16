from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from techinsight.application.search import SearchService


def _search_item(
    article_id: int,
    content_hash: str,
    published_at: datetime,
    keyword_score: float,
) -> dict:
    return {
        "articleId": article_id,
        "title": f"Article {article_id}",
        "author": "Ito",
        "category": "Backend",
        "contentPreview": "preview",
        "publishedAt": published_at,
        "semanticScore": 0.0,
        "keywordScore": keyword_score,
        "duplicateCount": 1 if content_hash == "same" else 0,
        "contentHash": content_hash,
    }


def _service_with_lexical_items(monkeypatch, lexical_items: list[dict]) -> SearchService:
    service = object.__new__(SearchService)
    service.settings = SimpleNamespace(search_rrf_k=60, lexical_candidate_limit=50)
    monkeypatch.setattr(service, "_merge_lexical_candidates", lambda **_kwargs: lexical_items)
    return service


def test_remove_duplicate_content_keeps_first_ranked_item() -> None:
    service = object.__new__(SearchService)

    items = [
        {"articleId": 10, "contentHash": "same", "finalScore": 0.9},
        {"articleId": 20, "contentHash": "other", "finalScore": 0.8},
        {"articleId": 30, "contentHash": "same", "finalScore": 0.7},
    ]

    unique_items = service._remove_duplicate_content(items)

    assert [item["articleId"] for item in unique_items] == [10, 20]


def test_search_excludes_duplicate_content_after_relevance_sort(monkeypatch) -> None:
    service = _service_with_lexical_items(
        monkeypatch,
        [
            _search_item(10, "same", datetime(2024, 1, 1, tzinfo=UTC), 0.9),
            _search_item(20, "other", datetime(2024, 1, 2, tzinfo=UTC), 0.8),
            _search_item(30, "same", datetime(2024, 1, 3, tzinfo=UTC), 0.7),
        ],
    )

    result = service.search(
        query="postgres",
        mode="keyword",
        categories=[],
        authors=[],
        published_from=None,
        published_to=None,
        page=1,
        page_size=20,
        sort="relevance",
        include_duplicates=False,
    )

    assert [item["articleId"] for item in result["items"]] == [10, 20]
    assert result["total"] == 2


def test_search_excludes_duplicate_content_after_newest_sort(monkeypatch) -> None:
    service = _service_with_lexical_items(
        monkeypatch,
        [
            _search_item(10, "same", datetime(2024, 1, 1, tzinfo=UTC), 0.9),
            _search_item(20, "other", datetime(2024, 1, 2, tzinfo=UTC), 0.8),
            _search_item(30, "same", datetime(2024, 1, 3, tzinfo=UTC), 0.7),
        ],
    )

    result = service.search(
        query="postgres",
        mode="keyword",
        categories=[],
        authors=[],
        published_from=None,
        published_to=None,
        page=1,
        page_size=20,
        sort="newest",
        include_duplicates=False,
    )

    assert [item["articleId"] for item in result["items"]] == [30, 20]
    assert result["total"] == 2
