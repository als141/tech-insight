from __future__ import annotations

import json
import os
import time
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx


def _wait_for_api(client: httpx.Client) -> None:
    last_error: Exception | None = None
    for _ in range(120):
        try:
            response = client.get("/health")
            if response.status_code == 200:
                return
        except httpx.HTTPError as exc:
            last_error = exc
        time.sleep(1)
    raise RuntimeError(f"API did not become ready: {last_error}")


def _assert_status(response: httpx.Response, status_code: int) -> dict[str, Any]:
    if response.status_code != status_code:
        raise AssertionError(
            f"{response.request.method} {response.request.url} returned "
            f"{response.status_code}: {response.text}"
        )
    if status_code == 204:
        return {}
    return response.json()


def _article_payload(prefix: str) -> dict[str, str]:
    return {
        "title": f"{prefix}: CRUD verification article",
        "content": (
            "This article is created by the Docker E2E test to verify create, "
            "read, update, and delete behaviour."
        ),
        "author": "E2E Tester",
        "category": "Backend",
        "published_at": datetime(2026, 1, 1, 9, 0, tzinfo=UTC).isoformat(),
    }


def main() -> None:
    base_url = os.getenv("E2E_API_BASE_URL", "http://backend:8000/api/v1")
    expected_initial_total = os.getenv("E2E_EXPECTED_INITIAL_TOTAL")
    created_id: int | None = None
    run_id = f"e2e-{uuid.uuid4().hex[:10]}"

    with httpx.Client(base_url=base_url, timeout=httpx.Timeout(300.0, connect=5.0)) as client:
        _wait_for_api(client)

        initial = _assert_status(client.get("/articles", params={"page": 1, "page_size": 1}), 200)
        initial_total = initial["total"]
        if expected_initial_total is not None and initial_total != int(expected_initial_total):
            raise AssertionError(
                f"Expected initial article total {expected_initial_total}, got {initial_total}"
            )

        try:
            created = _assert_status(client.post("/articles", json=_article_payload(run_id)), 201)
            created_id = created["id"]
            if created["title"] != f"{run_id}: CRUD verification article":
                raise AssertionError("Created article title did not match request payload")

            detail = _assert_status(client.get(f"/articles/{created_id}"), 200)
            if detail["id"] != created_id or not isinstance(detail["related_articles"], list):
                raise AssertionError("Created article detail response is malformed")

            updated_payload = _article_payload(f"{run_id}-updated")
            updated_payload["content"] = (
                "This article was updated by the Docker E2E test and should remain "
                "searchable until the delete step runs."
            )
            updated = _assert_status(
                client.put(f"/articles/{created_id}", json=updated_payload), 200
            )
            if updated["title"] != updated_payload["title"]:
                raise AssertionError("Updated article title did not match request payload")

            listed = _assert_status(
                client.get(
                    "/articles",
                    params={"page": 1, "page_size": 10, "keyword": f"{run_id}-updated"},
                ),
                200,
            )
            if created_id not in [item["id"] for item in listed["items"]]:
                raise AssertionError("Updated article was not returned by keyword list query")

            _assert_status(client.delete(f"/articles/{created_id}"), 204)
            created_id = None

            missing = client.get(f"/articles/{updated['id']}")
            if missing.status_code != 404:
                raise AssertionError(
                    f"Deleted article returned {missing.status_code}, expected 404"
                )

            final = _assert_status(client.get("/articles", params={"page": 1, "page_size": 1}), 200)
            if final["total"] != initial_total:
                raise AssertionError(
                    f"Article total did not return to baseline: {initial_total} -> {final['total']}"
                )
        finally:
            if created_id is not None:
                client.delete(f"/articles/{created_id}")

    print(
        json.dumps(
            {
                "status": "ok",
                "base_url": base_url,
                "initial_total": initial_total,
                "scenario": "article CRUD",
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
