from __future__ import annotations

from app.schemas.lead import LeadIn
from app.services.normalize import normalize_lead


def test_name_trimmed_and_collapsed() -> None:
    out = normalize_lead(LeadIn(name="  John   Doe  ", email="john@example.com"))
    assert out.name == "John Doe"


def test_email_lowercased_and_trimmed() -> None:
    out = normalize_lead(LeadIn(name="John", email="  John@Example.COM "))
    assert out.email == "john@example.com"


def test_phone_cleaned_with_plus() -> None:
    out = normalize_lead(LeadIn(name="John", phone="+1 (234) 567-890"))
    assert out.phone == "+1234567890"


def test_phone_cleaned_without_plus() -> None:
    out = normalize_lead(LeadIn(name="John", phone="050 123 45 67"))
    assert out.phone == "0501234567"


def test_message_strip_only_preserves_internal_newlines() -> None:
    out = normalize_lead(LeadIn(name="John", email="a@b.com", message="  hi\n\nthere  "))
    assert out.message == "hi\n\nthere"


def test_empty_optional_becomes_none() -> None:
    out = normalize_lead(LeadIn(name="John", email="a@b.com", phone="()"))
    assert out.phone is None


def test_source_collapsed_and_empty_to_none() -> None:
    out1 = normalize_lead(LeadIn(name="John", email="a@b.com", source="  google   ads "))
    assert out1.source == "google ads"
    out2 = normalize_lead(LeadIn(name="John", email="a@b.com", source="   "))
    assert out2.source is None


def test_meta_passthrough() -> None:
    out = normalize_lead(LeadIn(name="John", email="a@b.com", meta={"utm": "x"}))
    assert out.meta == {"utm": "x"}

