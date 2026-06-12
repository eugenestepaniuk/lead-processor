import pytest
from pydantic import ValidationError

from app.schemas.lead import LeadIn


def test_valid_with_email_only() -> None:
    lead = LeadIn(name="John Doe", email="john@example.com")
    assert lead.name == "John Doe"
    assert lead.email == "john@example.com"
    assert lead.phone is None


def test_valid_with_phone_only() -> None:
    lead = LeadIn(name="John Doe", phone="+1234567890")
    assert lead.name == "John Doe"
    assert lead.phone == "+1234567890"
    assert lead.email is None


def test_missing_name_raises() -> None:
    with pytest.raises(ValidationError):
        LeadIn(email="john@example.com")


def test_empty_name_raises() -> None:
    with pytest.raises(ValidationError):
        LeadIn(name="", email="john@example.com")


def test_no_contact_raises() -> None:
    with pytest.raises(ValidationError):
        LeadIn(name="John Doe")


# --- Bounded field tests ---

def test_name_too_long_raises() -> None:
    with pytest.raises(ValidationError):
        LeadIn(name="A" * 201, email="a@example.com")


def test_name_max_length_passes() -> None:
    lead = LeadIn(name="A" * 200, email="a@example.com")
    assert len(lead.name) == 200


def test_message_too_long_raises() -> None:
    with pytest.raises(ValidationError):
        LeadIn(name="Jane", email="jane@example.com", message="x" * 5001)


def test_message_max_length_passes() -> None:
    lead = LeadIn(name="Jane", email="jane@example.com", message="x" * 5000)
    assert lead.message is not None and len(lead.message) == 5000


def test_source_too_long_raises() -> None:
    with pytest.raises(ValidationError):
        LeadIn(name="Jane", email="jane@example.com", source="s" * 201)


def test_source_max_length_passes() -> None:
    lead = LeadIn(name="Jane", email="jane@example.com", source="s" * 200)
    assert lead.source is not None and len(lead.source) == 200


def test_meta_too_many_keys_raises() -> None:
    with pytest.raises(ValidationError):
        LeadIn(
            name="Jane",
            email="jane@example.com",
            meta={str(i): i for i in range(21)},
        )


def test_meta_twenty_keys_passes() -> None:
    lead = LeadIn(
        name="Jane",
        email="jane@example.com",
        meta={str(i): i for i in range(20)},
    )
    assert lead.meta is not None and len(lead.meta) == 20


def test_valid_lead_with_all_fields_passes() -> None:
    lead = LeadIn(
        name="Alice",
        email="alice@example.com",
        phone="+1234567890",
        message="Hello",
        source="landing",
        meta={"utm_source": "google"},
    )
    assert lead.name == "Alice"


