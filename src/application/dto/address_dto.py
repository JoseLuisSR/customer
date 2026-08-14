import uuid

from pydantic import BaseModel, ConfigDict, Field


class AddressRqst(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    country: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=100)
    city: str = Field(min_length=2, max_length=100)
    address: str = Field(min_length=3, max_length=200)
    postal_code: str = Field(alias="postal-code", min_length=3, max_length=15)


class AddressPatchRqst(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    country: str | None = None
    state: str | None = None
    city: str | None = None
    address: str | None = None
    postal_code: str | None = Field(default=None, alias="postal-code")


class AddressRsps(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    country: str
    state: str
    city: str
    address: str
    postal_code: str = Field(alias="postal-code")
