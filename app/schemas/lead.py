from __future__ import annotations

from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class LeadIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)   # required, rejects empty/overlong
    email: EmailStr | None = None                      # optional
    phone: str | None = Field(default=None, max_length=32)    # optional
    message: str | None = Field(default=None, max_length=5000)  # optional
    source: str | None = Field(default=None, max_length=200)    # optional (lead origin)
    meta: dict[str, Any] | None = None                 # optional (e.g. utm tags)

    @field_validator("meta")
    @classmethod
    def _limit_meta_keys(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        if v is not None and len(v) > 20:
            raise ValueError("meta accepts at most 20 keys")
        return v

    @model_validator(mode="after")
    def _require_contact(self) -> LeadIn:
        if self.email is None and self.phone is None:
            raise ValueError("at least one contact is required: email or phone")
        return self
