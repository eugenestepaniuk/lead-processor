"""SQLite storage helper — connection factory, schema initialisation, and INSERT.

Connection helper + leads table creation.
Save_lead INSERT helper.
"""

from __future__ import annotations

import json
import logging
import pathlib
import sqlite3
from datetime import UTC, datetime

from app.config import get_settings
from app.schemas.ai_result import AIResult
from app.schemas.lead import LeadIn

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_CREATE_LEADS_TABLE = """
CREATE TABLE IF NOT EXISTS leads (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  TEXT NOT NULL,
    name        TEXT NOT NULL,
    email       TEXT,
    phone       TEXT,
    message     TEXT,
    source      TEXT,
    meta        TEXT,
    summary     TEXT,
    category    TEXT,
    reason      TEXT
)
"""

_INSERT_LEAD = (
    "INSERT INTO leads "
    "(created_at, name, email, phone, message, source, meta, summary, category, reason) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_connection() -> sqlite3.Connection:
    """Open and return a new SQLite connection to the configured database.

    The parent directory is created automatically if it does not exist.
    The **caller** is responsible for closing the connection.

    Returns:
        An open :class:`sqlite3.Connection`.
    """
    db_path = pathlib.Path(get_settings().sqlite_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(db_path)


def init_db() -> None:
    """Create the ``leads`` table if it does not already exist.

    Opens a fresh connection, executes the CREATE TABLE statement, commits,
    and closes the connection.  Exceptions propagate — DB initialisation
    failure is critical and must not be silenced.
    """
    conn = get_connection()
    try:
        conn.execute(_CREATE_LEADS_TABLE)
        conn.commit()
        logger.info("SQLite leads table initialized")
    finally:
        conn.close()


def save_lead(lead: LeadIn, ai: AIResult | None) -> int:
    """Insert a lead row into the ``leads`` table and return its new id.

    Args:
        lead: The validated, normalised inbound lead.
        ai:   The AI analysis result, or ``None`` when AI did not run.

    Returns:
        The auto-generated integer primary key of the inserted row.

    Raises:
        RuntimeError: If the database does not return a row id after INSERT.
    """
    created_at = datetime.now(UTC).isoformat()
    meta_json = json.dumps(lead.meta) if lead.meta is not None else None

    category = ai.category if ai is not None else None
    summary = ai.summary if ai is not None else None
    reason = ai.reason if ai is not None else None

    conn = get_connection()
    try:
        cursor = conn.execute(
            _INSERT_LEAD,
            (created_at, lead.name, lead.email, lead.phone,
             lead.message, lead.source, meta_json, summary, category, reason),
        )
        conn.commit()
        row_id = cursor.lastrowid
        if row_id is None:
            raise RuntimeError("INSERT into leads did not return a row id")
        logger.info("Lead saved (id=%s)", row_id)
        return row_id
    finally:
        conn.close()


