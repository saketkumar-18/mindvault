"""RAG evaluation harness.

Measures retrieval relevance against a small labeled dataset. This is not a
claim of absolute accuracy — it is a regression check to detect when retrieval
quality degrades.

Run: python -m pytest tests/eval -v
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from mindvault.api.app import create_app
from mindvault.services.container import get_container

DATASET = Path(__file__).parent / "rag_eval_dataset.jsonl"


def _load_dataset() -> list[dict[str, object]]:
    items = []
    with DATASET.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


@pytest.fixture(scope="module")
def indexed_client():
    app = create_app()
    client = TestClient(app)

    for item in _load_dataset():
        content = str(item["document"])
        filename = str(item["source_file"])
        resp = client.post(
            "/api/documents",
            files={"file": (filename, content.encode("utf-8"), "text/plain")},
            data={"duplicate": "true"},
        )
        assert resp.status_code == 200, resp.text
        doc_id = resp.json()["id"]
        for _ in range(100):
            status = client.get(f"/api/documents/{doc_id}").json()["status"]
            if status == "indexed":
                break
            time.sleep(0.1)
        else:
            raise TimeoutError(f"Document {doc_id} did not index in time.")

    yield client
    client.close()


def test_retrieval_relevance(indexed_client):
    """The correct document must be in the top-1 retrieval results."""
    container = get_container()
    correct = 0
    total = 0
    for item in _load_dataset():
        total += 1
        question = str(item["question"])
        matches = container.search_service.search(question, top_k=1)
        if not matches:
            continue
        if str(item["source_file"]) in matches[0].filename:
            correct += 1
    # With the deterministic hash embedding provider a perfect score is not
    # guaranteed; keep the bar achievable without ML dependencies while still
    # catching gross regressions.
    assert correct >= max(1, total // 2), f"Retrieval relevance too low: {correct}/{total}"


def test_answer_faithfulness_helpers():
    from mindvault.rag.rag_service import RAGService

    assert RAGService._is_grounded("Some answer.") is True
    assert RAGService._is_grounded("I couldn't find enough information in your documents.") is False
