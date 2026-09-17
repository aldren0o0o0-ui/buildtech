from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class AddressBase(BaseModel):
    label: Optional[str] = Field(None, max_length=50, description="e.g. Home, Work, Office")
    recipient_name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=7, max_length=25)
    address_line1: str = Field(..., min_length=3, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    barangay: str = Field(..., min_length=1, max_length=100)
    city: str = Field(..., min_length=1, max_length=100)
    province: str = Field(..., min_length=1, max_length=100)
    postal_code: str = Field(..., min_length=3, max_length=20)
    country: str = Field(default="Philippines", min_length=2, max_length=100)
    is_default: bool = False

    @field_validator(
        "recipient_name",
        "phone",
        "address_line1",
        "barangay",
        "city",
        "province",
        "postal_code",
        "country",
        mode="before",
    )
    @classmethod
    def strip_and_validate_required_non_empty(cls, v: str) -> str:
        if isinstance(v, str):
            v_stripped = v.strip()
            if not v_stripped:
                raise ValueError("Field cannot be empty or whitespace only")
            return v_stripped
        return v

    @field_validator("label", "address_line2", mode="before")
    @classmethod
    def strip_optional(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            v_stripped = v.strip()
            return v_stripped if v_stripped else None
        return v


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    label: Optional[str] = Field(None, max_length=50)
    recipient_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, min_length=7, max_length=25)
    address_line1: Optional[str] = Field(None, min_length=3, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    barangay: Optional[str] = Field(None, min_length=1, max_length=100)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    province: Optional[str] = Field(None, min_length=1, max_length=100)
    postal_code: Optional[str] = Field(None, min_length=3, max_length=20)
    country: Optional[str] = Field(None, min_length=2, max_length=100)
    is_default: Optional[bool] = None

    @field_validator(
        "recipient_name",
        "phone",
        "address_line1",
        "barangay",
        "city",
        "province",
        "postal_code",
        "country",
        mode="before",
    )
    @classmethod
    def strip_and_validate_optional_non_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and isinstance(v, str):
            v_stripped = v.strip()
            if not v_stripped:
                raise ValueError("Field cannot be empty or whitespace only")
            return v_stripped
        return v

    @field_validator("label", "address_line2", mode="before")
    @classmethod
    def strip_optional_fields(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            v_stripped = v.strip()
            return v_stripped if v_stripped else None
        return v


class AddressResponse(AddressBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
