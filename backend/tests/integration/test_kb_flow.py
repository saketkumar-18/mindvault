"""Knowledge base CRUD and knowledge base document assignment."""

from fastapi.testclient import TestClient


def test_kb_crud(client: TestClient):
    # Create
    resp = client.post("/api/knowledge-bases", params={"name": "Test KB", "description": "For testing"})
    assert resp.status_code == 200, resp.text
    kb_id = resp.json()["id"]

    # List
    resp = client.get("/api/knowledge-bases")
    assert resp.status_code == 200
    ids = [kb["id"] for kb in resp.json()["knowledge_bases"]]
    assert kb_id in ids

    # Rename
    resp = client.patch(f"/api/knowledge-bases/{kb_id}", params={"name": "Renamed KB"})
    resp = client.get(f"/api/knowledge-bases/{kb_id}")
    assert resp.json()["name"] == "Renamed KB"

    # Delete
    resp = client.delete(f"/api/knowledge-bases/{kb_id}")
    assert resp.status_code == 200
    resp = client.get(f"/api/knowledge-bases/{kb_id}")
    assert resp.status_code == 404


def test_kb_document_assignment(client: TestClient):
    # Create KB
    resp = client.post("/api/knowledge-bases", params={"name": "Assignment KB"})
    kb_id = resp.json()["id"]

    # Upload document
    resp = client.post(
        "/api/documents",
        files={"file": ("doc.txt", b"test content", "text/plain")},
        data={"knowledge_base_id": kb_id},
    )
    doc_id = resp.json()["id"]

    # Verify document is in KB
    resp = client.get(f"/api/knowledge-bases/{kb_id}")
    stats = resp.json()["statistics"]
    assert stats["document_count"] >= 1

    # Remove document from KB
    resp = client.delete(f"/api/knowledge-bases/{kb_id}/documents/{doc_id}")
    assert resp.status_code == 200

    # Cleanup
    client.delete(f"/api/documents/{doc_id}")
    client.delete(f"/api/knowledge-bases/{kb_id}")