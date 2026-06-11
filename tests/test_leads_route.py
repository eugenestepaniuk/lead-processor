from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_valid_lead_returns_200() -> None:
    resp = client.post("/api/leads", json={"name": "John Doe", "email": "john@example.com"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["received"]["name"] == "John Doe"
    assert body["received"]["email"] == "john@example.com"


def test_missing_name_returns_422() -> None:
    resp = client.post("/api/leads", json={"email": "john@example.com"})
    assert resp.status_code == 422


def test_empty_name_returns_422() -> None:
    resp = client.post("/api/leads", json={"name": "", "email": "john@example.com"})
    assert resp.status_code == 422


def test_no_contact_returns_422() -> None:
    resp = client.post("/api/leads", json={"name": "John Doe"})
    assert resp.status_code == 422

