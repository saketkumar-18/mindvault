"""Study generation and jobs endpoint tests."""

import json
import time

from fastapi.testclient import TestClient


def _upload_txt(client: TestClient, name: str = "notes.txt", content: str = "Machine learning is a subset of AI."):
    resp = client.post("/api/documents", files={"file": (name, content.encode(), "text/plain")})
    doc_id = resp.json()["id"]
    for _ in range(30):
        status = client.get(f"/api/documents/{doc_id}").json()["status"]
        if status == "indexed":
            break
        time.sleep(0.3)
    return doc_id


def test_study_summary(client: TestClient):
    doc_id = _upload_txt(client)
    resp = client.post("/api/study/generate", json={"kind": "summary", "document_id": doc_id})
    assert resp.status_code == 200, resp.text
    material = resp.json()
    assert material["id"]
    assert "text" in json.loads(material["content"]) or material["content"]

    # List materials
    resp = client.get("/api/study/materials")
    assert resp.status_code == 200
    assert len(resp.json()["materials"]) >= 1

    # Delete material
    resp = client.delete(f"/api/study/materials/{material['id']}")
    assert resp.status_code == 200

    client.delete(f"/api/documents/{doc_id}")


def test_study_invalid_kind(client: TestClient):
    doc_id = _upload_txt(client)
    resp = client.post("/api/study/generate", json={"kind": "nonexistent", "document_id": doc_id})
    assert resp.status_code == 422
    client.delete(f"/api/documents/{doc_id}")


def test_jobs_listing(client: TestClient):
    doc_id = _upload_txt(client)
    resp = client.get("/api/jobs")
    assert resp.status_code == 200
    jobs = resp.json()["jobs"]
    assert len(jobs) >= 1
    assert jobs[0]["kind"] in ("index", "reindex")
    client.delete(f"/api/documents/{doc_id}")


def test_streaming_chat(client: TestClient):
    doc_id = _upload_txt(client, content="Zero trust architecture assumes no device is trusted by default.")
    with client.stream("POST", "/api/chat", json={"message": "What is zero trust?", "stream": True}) as resp:
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        body = "".join(resp.iter_text())
    assert "data: " in body
    assert "token" in body
    client.delete(f"/api/documents/{doc_id}")


def test_regenerate(client: TestClient):
    doc_id = _upload_txt(client, content="Rust is a memory-safe systems programming language.")
    resp = client.post("/api/chat", json={"message": "What is Rust?", "stream": False})
    assert resp.status_code == 200
    conversation_id = resp.json()["conversation_id"]

    # Regenerate
    resp = client.post(f"/api/chat/{conversation_id}/regenerate?stream=false")
    assert resp.status_code == 200
    assert resp.json()["conversation_id"] == conversation_id
    client.delete(f"/api/documents/{doc_id}")


def test_compare_documents(client: TestClient):
    doc_a = _upload_txt(client, name="a.txt", content="Python is a high-level programming language.")
    doc_b = _upload_txt(client, name="b.txt", content="Rust is a systems programming language with memory safety.")

    resp = client.post("/api/study/compare", json={"document_ids": [doc_a, doc_b]})
    assert resp.status_code == 200, resp.text
    material = resp.json()
    assert material["kind"] == "comparison"
    assert "text" in material["content"]

    # Single document should fail
    resp = client.post("/api/study/compare", json={"document_ids": [doc_a]})
    assert resp.status_code == 422

    client.delete(f"/api/documents/{doc_a}")
    client.delete(f"/api/documents/{doc_b}")


def test_resume_analysis(client: TestClient):
    resume = _upload_txt(client, name="resume.txt", content="Python developer with 5 years experience in FastAPI.")
    jd = _upload_txt(client, name="job.txt", content="We need a Python developer skilled in FastAPI and Docker.")

    resp = client.post(
        "/api/study/resume-analysis",
        json={"resume_document_id": resume, "job_description_document_id": jd},
    )
    assert resp.status_code == 200, resp.text
    material = resp.json()
    assert material["kind"] == "resume_analysis"

    # Missing both docs should fail
    resp = client.post(
        "/api/study/resume-analysis",
        json={"resume_document_id": resume, "job_description_document_id": "00000000000000000000000000000000"},
    )
    assert resp.status_code == 404

    client.delete(f"/api/documents/{resume}")
    client.delete(f"/api/documents/{jd}")