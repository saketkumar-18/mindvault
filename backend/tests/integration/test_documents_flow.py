"""End-to-end document upload, indexing, search, and chat flow."""

from fastapi.testclient import TestClient


def test_upload_txt(client: TestClient):
    # Upload a plain text file
    content = b"MindVault is a private AI assistant. It runs entirely on your local machine."
    resp = client.post("/api/documents", files={"file": ("test.txt", content, "text/plain")})
    assert resp.status_code == 200, resp.text
    doc_id = resp.json()["id"]
    assert doc_id
    assert len(doc_id) == 32

    # Wait for indexing (poll status)
    import time

    for _ in range(30):
        resp = client.get(f"/api/documents/{doc_id}")
        assert resp.status_code == 200
        status = resp.json()["status"]
        if status == "indexed":
            break
        time.sleep(0.3)
    else:
        # Check error
        resp = client.get(f"/api/documents/{doc_id}")
        assert resp.json()["status"] == "indexed", f"Indexing failed: {resp.json().get('error')}"

    # Search
    resp = client.post("/api/search", json={"query": "private AI assistant"})
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) > 0
    assert "test.txt" in results[0]["filename"]

    # Chat
    resp = client.post("/api/chat", json={"message": "What is MindVault?", "stream": False})
    assert resp.status_code == 200
    data = resp.json()
    assert "conversation_id" in data
    # Mock provider returns a deterministic answer
    assert "Based on the provided documents" in data.get("text", "")

    # Verify conversation was persisted
    resp = client.get("/api/conversations")
    convs = resp.json()["conversations"]
    assert len(convs) == 1
    assert convs[0]["message_count"] >= 2  # user + assistant

    # Delete document
    resp = client.delete(f"/api/documents/{doc_id}")
    assert resp.status_code == 200

    # Verify deletion
    resp = client.get(f"/api/documents/{doc_id}")
    assert resp.status_code == 404


def test_upload_duplicate(client: TestClient):
    content = b"Hello world."
    resp = client.post("/api/documents", files={"file": ("a.txt", content, "text/plain")})
    assert resp.status_code == 200
    resp = client.post("/api/documents", files={"file": ("a.txt", content, "text/plain")})
    assert resp.status_code == 409
    assert "duplicate" in resp.text.lower() or "already exists" in resp.text.lower()