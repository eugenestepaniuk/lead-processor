from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.pipeline.process_lead import ProcessResult


def test_valid_lead_returns_200(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = ProcessResult(
        lead_id=7, summary="S", category="warm", ai_ran=True, notified=True
    )

    import app.routes.leads as leads_mod
    monkeypatch.setattr(leads_mod, "process_lead", lambda payload: expected)

    client = TestClient(app)
    resp = client.post("/api/leads", json={"name": "John Doe", "email": "john@example.com"})
    assert resp.status_code == 200
    assert resp.json() == expected.model_dump()


def test_missing_name_returns_422() -> None:
    client = TestClient(app)
    resp = client.post("/api/leads", json={"email": "john@example.com"})
    assert resp.status_code == 422


def test_empty_name_returns_422() -> None:
    client = TestClient(app)
    resp = client.post("/api/leads", json={"name": "", "email": "john@example.com"})
    assert resp.status_code == 422


def test_no_contact_returns_422() -> None:
    client = TestClient(app)
    resp = client.post("/api/leads", json={"name": "John Doe"})
    assert resp.status_code == 422


def test_health_returns_200() -> None:
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_init_db_called_on_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict[str, bool] = {"v": False}

    def fake_init_db() -> None:
        called["v"] = True

    monkeypatch.setattr("app.main.init_db", fake_init_db)
    with TestClient(app) as client:
        client.get("/health")
    assert called["v"] is True


