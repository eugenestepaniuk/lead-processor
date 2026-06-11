from __future__ import annotations

import re

from app.schemas.lead import LeadIn


def _collapse_ws(value: str) -> str:
    """Collapse runs of whitespace to a single space, then strip."""
    return re.sub(r"\s+", " ", value).strip()


def _norm_optional_text(value: str | None, *, collapse: bool) -> str | None:
    """Normalize an optional free-text field; empty result becomes None."""
    if value is None:
        return None
    cleaned = _collapse_ws(value) if collapse else value.strip()
    return cleaned or None


def _norm_email(value: str | None) -> str | None:
    """Strip and lowercase the whole email string; empty result becomes None."""
    if value is None:
        return None
    cleaned = value.strip().lower()
    return cleaned or None


def _norm_phone(value: str | None) -> str | None:
    """Approximate E.164 phone cleaning (NOT real validation).

    Keeps a leading '+' if present; strips all non-digit characters;
    returns None if no digits remain.
    """
    if value is None:
        return None
    stripped = value.strip()
    has_plus = stripped.startswith("+")
    digits = re.sub(r"\D", "", stripped)
    if not digits:
        return None
    return f"+{digits}" if has_plus else digits


def normalize_lead(lead: LeadIn) -> LeadIn:
    """Return a new LeadIn with normalized field values.

    Uses model_copy(update=...) to bypass re-validation — normalization
    must never raise.
    """
    return lead.model_copy(
        update={
            "name": _collapse_ws(lead.name),
            "email": _norm_email(lead.email),
            "phone": _norm_phone(lead.phone),
            "message": _norm_optional_text(lead.message, collapse=False),
            "source": _norm_optional_text(lead.source, collapse=True),
        }
    )

