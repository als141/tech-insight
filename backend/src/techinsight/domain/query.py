from __future__ import annotations

import hashlib
import re


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_query_text(value: str) -> str:
    return normalize_whitespace(value).lower()


def normalize_document_text(value: str) -> str:
    return normalize_whitespace(value)


def format_document_text(title: str, category: str, content: str) -> str:
    return normalize_document_text(f"title: {title} | text: {category} | {content}")


def format_query_text(query: str) -> str:
    return normalize_query_text(f"task: search result | query: {query}")


def build_content_hash(title: str, content: str) -> str:
    return stable_hash(f"{normalize_whitespace(title)}\n{normalize_whitespace(content)}")
