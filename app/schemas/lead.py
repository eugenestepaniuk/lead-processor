from __future__ import annotations

from typing import Any

from pydantic import BaseModel, EmailStr, Field, model_validator


class LeadIn(BaseModel):
    name: str = Field(min_length=1)        # required, rejects empty string
    email: EmailStr | None = None          # optional
    phone: str | None = None               # optional
    message: str | None = None             # optional
    source: str | None = None              # optional (where the lead came from)
    meta: dict[str, Any] | None = None     # optional (e.g. utm tags)

    @model_validator(mode="after")
    def _require_contact(self) -> LeadIn:
        if self.email is None and self.phone is None:
            raise ValueError("at least one contact is required: email or phone")
        return self

