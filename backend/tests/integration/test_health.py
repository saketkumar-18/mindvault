"""Health endpoint tests."""

from fastapi.testclient import TestClient


def test_health(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


def test_liveness(client: TestClient):
    resp = client.get("/liveness")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_readiness(client: TestClient):
    resp = client.get("/readiness")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"