from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from techinsight.api.deps import get_app_settings, get_embedding_provider
from techinsight.config.settings import Settings
from techinsight.infrastructure.db import get_db
from techinsight.main import app


class DummySession:
    def execute(self, *_args, **_kwargs) -> int:
        return 1


class DummyProvider:
    model_name = "Qwen/Qwen3-Embedding-0.6B"


def override_db():
    yield DummySession()


def test_health_endpoint() -> None:
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_app_settings] = lambda: Settings(embedding_provider="qwen")
    app.dependency_overrides[get_embedding_provider] = lambda: DummyProvider()

    client = TestClient(app)
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    app.dependency_overrides.clear()


def test_search_endpoint(monkeypatch) -> None:
    captured_kwargs = {}

    class FakeSearchService:
        def search(self, **kwargs):
            captured_kwargs.update(kwargs)
            return {
                "items": [
                    {
                        "articleId": 1,
                        "title": "Implementing PostgreSQL",
                        "author": "Ito",
                        "category": "Backend",
                        "contentPreview": "schema design",
                        "publishedAt": datetime(2025, 1, 2, tzinfo=UTC),
                        "semanticScore": 0.9,
                        "keywordScore": 0.4,
                        "finalScore": 0.91,
                        "duplicateCount": 0,
                        "matchedBy": ["semantic", "keyword"],
                    }
                ],
                "total": 1,
            }

    monkeypatch.setattr(
        "techinsight.api.routes.get_search_service",
        lambda _session: FakeSearchService(),
    )
    app.dependency_overrides[get_db] = override_db

    client = TestClient(app)
    response = client.post(
        "/api/v1/search",
        json={
            "query": "PostgreSQL optimization",
            "mode": "hybrid",
            "filters": {
                "category": [],
                "author": [],
                "publishedFrom": None,
                "publishedTo": None,
            },
            "sort": "relevance",
            "includeDuplicates": False,
            "page": 1,
            "pageSize": 20,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["matchedBy"] == ["semantic", "keyword"]
    assert captured_kwargs["include_duplicates"] is False

    app.dependency_overrides.clear()
