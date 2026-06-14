"""API tests using FastAPI's TestClient.

The RAG layer and the index builder are stubbed so tests run with no model,
index, or Groq key.
"""
import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app


@pytest.fixture(autouse=True)
def stub_rag(monkeypatch):
    # Don't load the real pipeline (model + FAISS index) at startup.
    monkeypatch.setattr(main_module.rag, "load_pipeline", lambda: None)
    monkeypatch.setattr(main_module.rag, "is_ready", lambda: True)
    monkeypatch.setattr(main_module.rag, "reload_index", lambda: None)
    # Stub the (heavy) index build used by /reindex.
    monkeypatch.setattr(main_module, "build_index_fn", lambda *a, **k: 3)
    main_module._reindex_status.update(state="idle", detail="", vectors=None)

    def fake_answer(question, k=None):
        return {
            "answer": f"stub answer to: {question}",
            "sources": [
                {"url": "https://stackoverflow.com/questions/1", "title": "Q", "score": 10}
            ],
        }

    monkeypatch.setattr(main_module.rag, "answer", fake_answer)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ask_returns_answer_and_sources(client):
    r = client.post("/ask", json={"question": "How do I reverse a list in Python?"})
    assert r.status_code == 200
    body = r.json()
    assert "reverse a list" in body["answer"]
    assert len(body["sources"]) >= 1
    assert body["sources"][0]["url"].startswith("https://stackoverflow.com")


def test_ask_respects_top_k_field(client):
    r = client.post("/ask", json={"question": "What is a tuple?", "top_k": 3})
    assert r.status_code == 200


def test_ask_empty_question_rejected(client):
    r = client.post("/ask", json={"question": ""})
    assert r.status_code == 422


def test_ask_missing_question_rejected(client):
    r = client.post("/ask", json={})
    assert r.status_code == 422


def test_ask_top_k_out_of_range_rejected(client):
    r = client.post("/ask", json={"question": "hi", "top_k": 99})
    assert r.status_code == 422


def test_reindex_status_idle_by_default(client):
    assert client.get("/reindex/status").json()["state"] == "idle"


def test_reindex_starts_and_completes(client):
    r = client.post("/reindex", json={"max_docs": 100})
    assert r.status_code == 200
    assert r.json()["state"] == "started"
    # Under TestClient the background task runs synchronously.
    status = client.get("/reindex/status").json()
    assert status["state"] == "done"
    assert status["vectors"] == 3
