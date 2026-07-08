import re

from pydantic import BaseModel, HttpUrl, field_validator


class LinkCreate(BaseModel):
    url: HttpUrl
    custom_code: str | None = None

    @field_validator("custom_code")
    @classmethod
    def validate_custom_code(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not re.match(r"^[A-Za-z0-9]{3,20}$", v):
            raise ValueError("custom_code must be alphanumeric and 3-20 characters")
        return v


class LinkResponse(BaseModel):
    code: str
    url: str
    short_url: str
    created_at: str
    visit_count: int
