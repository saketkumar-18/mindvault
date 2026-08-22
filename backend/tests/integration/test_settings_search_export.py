"""Settings and search export tests."""

from fastapi.testclient import TestClient


def test_settings(client: TestClient):
    resp = client.get("/api/settings")
    assert resp.status_code == 200
    data = resp.json()
    assert "settings" in data

    # Update a setting
    resp = client.put("/api/settings", json={"retrieval": {"top_k": 5}})
    assert resp.status_code == 200
    assert resp.json()["settings"]["retrieval"]["top_k"] == 5

    # Reset
    resp = client.post("/api/settings/reset")
    assert resp.status_code == 200


def test_export(client: TestClient):
    # Upload a doc first, then we can test export
    client.post("/api/documents", files={"file": ("export.txt", b"export test", "text/plain")})

    resp = client.get("/api/export/conversations")
    assert resp.status_code == 200
    assert "conversations" in resp.json()

    resp = client.get("/api/export/knowledge-bases")
    assert resp.status_code == 200
    assert "knowledge_bases" in resp.json()

    resp = client.get("/api/export/all")
    assert resp.status_code == 200
    content_type = resp.headers.get("content-type", "")
    assert "application/zip" in content_type


def test_system_info(client: TestClient):
    resp = client.get("/api/system/info")
    assert resp.status_code == 200
    data = resp.json()
    assert "os" in data
    assert "storage" in data
    assert "model" in data


def test_system_stats(client: TestClient):
    resp = client.get("/api/system/stats")
    assert resp.status_code == 200
    assert "documents" in resp.json()


def test_first_run_flow(client: TestClient):
    resp = client.get("/api/system/first-run")
    assert resp.status_code == 200
    assert "completed" in resp.json()

    resp = client.post("/api/system/first-run/complete")
    assert resp.status_code == 200

    resp = client.get("/api/system/first-run")
    assert resp.json()["completed"] is True


def test_clear_all_data(client: TestClient):
    # Upload a document and create a conversation
    client.post("/api/documents", files={"file": ("wipe.txt", b"wipe me", "text/plain")})
    client.post("/api/chat", json={"message": "Hello", "stream": False})
    client.put("/api/settings", json={"ai": {"temperature": 0.4}})

    # Refuse without confirm
    resp = client.delete("/api/system/data")
    assert resp.status_code == 422

    # Clear with confirm
    resp = client.delete("/api/system/data?confirm=DELETE")
    assert resp.status_code == 200

    stats = client.get("/api/system/stats").json()
    assert stats["documents"] == 0
    assert stats["conversations"] == 0
    assert stats["vector_chunks"] == 0