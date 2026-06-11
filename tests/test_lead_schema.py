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

