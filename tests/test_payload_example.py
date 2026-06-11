from __future__ import annotations

import json
from pathlib import Path

from app.schemas.lead import LeadIn


def test_example_payload_validates() -> None:
    path = Path(__file__).resolve().parent.parent / "examples" / "payload.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    lead = LeadIn.model_validate(data)

    assert lead.name == "Olena Kovalenko"
    # "email or phone" rule: both contacts present here
    assert lead.email is not None
    assert lead.phone is not None
    assert lead.meta is not None
    assert "utm_source" in lead.meta

