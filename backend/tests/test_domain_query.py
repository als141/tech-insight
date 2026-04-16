from __future__ import annotations

from techinsight.domain.query import build_content_hash, normalize_query_text


def test_normalize_query_text_only_normalizes_case_and_whitespace() -> None:
    normalized = normalize_query_text("  PostgreSQL   optimization  ")
    assert normalized == "postgresql optimization"


def test_normalize_query_text_keeps_original_terms() -> None:
    normalized = normalize_query_text("k8s と postgres の話")
    assert normalized == "k8s と postgres の話"


def test_content_hash_is_stable() -> None:
    first = build_content_hash("Hello", "World")
    second = build_content_hash(" Hello ", "World")
    assert first == second
