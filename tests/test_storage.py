"""Tests for app/services/storage.py — Block 5, subtasks 5.1 & 5.2."""

from __future__ import annotations

import sqlite3

from app.config import get_settings
from app.schemas.ai_result import AIResult
from app.schemas.lead import LeadIn


def test_init_db_creates_leads_table(tmp_path, monkeypatch):  # type: ignore[no-untyped-def]
    db_file = tmp_path / "leads.db"
    monkeypatch.setenv("SQLITE_PATH", str(db_file))
    get_settings.cache_clear()
    try:
        from app.services.storage import init_db

        init_db()

        assert db_file.exists()
        conn = sqlite3.connect(db_file)
        try:
            row = conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='leads'"
            ).fetchone()
            assert row is not None
        finally:
            conn.close()
    finally:
        get_settings.cache_clear()


def _column(conn: sqlite3.Connection, row_id: int, col: str) -> object:
    return conn.execute(
        f"SELECT {col} FROM leads WHERE id = ?", (row_id,)  # noqa: S608
    ).fetchone()[0]


def test_save_lead_inserts_row(tmp_path, monkeypatch):  # type: ignore[no-untyped-def]
    db_file = tmp_path / "leads.db"
    monkeypatch.setenv("SQLITE_PATH", str(db_file))
    get_settings.cache_clear()
    try:
        from app.services.storage import init_db, save_lead

        init_db()
        lead = LeadIn(
            name="Jane Doe",
            email="jane@example.com",
            phone="+15551234567",
            message="Interested in the premium plan",
            source="landing",
            meta={"utm_source": "google"},
        )
        ai = AIResult(category="hot", summary="Wants premium plan", reason="Buying intent")

        row_id = save_lead(lead, ai)
        assert isinstance(row_id, int)

        conn = sqlite3.connect(db_file)
        try:
            assert _column(conn, row_id, "name") == "Jane Doe"
            assert _column(conn, row_id, "email") == "jane@example.com"
            assert _column(conn, row_id, "phone") == "+15551234567"
            assert _column(conn, row_id, "category") == "hot"
            assert _column(conn, row_id, "summary") == "Wants premium plan"
            assert _column(conn, row_id, "meta") == '{"utm_source": "google"}'
            assert _column(conn, row_id, "created_at") is not None
        finally:
            conn.close()
    finally:
        get_settings.cache_clear()


def test_save_lead_without_ai_stores_nulls(tmp_path, monkeypatch):  # type: ignore[no-untyped-def]
    db_file = tmp_path / "leads.db"
    monkeypatch.setenv("SQLITE_PATH", str(db_file))
    get_settings.cache_clear()
    try:
        from app.services.storage import init_db, save_lead

        init_db()
        lead = LeadIn(name="No AI", phone="+15550000000")
        row_id = save_lead(lead, None)

        conn = sqlite3.connect(db_file)
        try:
            assert _column(conn, row_id, "category") is None
            assert _column(conn, row_id, "summary") is None
            assert _column(conn, row_id, "reason") is None
            assert _column(conn, row_id, "name") == "No AI"
        finally:
            conn.close()
    finally:
        get_settings.cache_clear()


