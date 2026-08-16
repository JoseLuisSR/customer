import uuid

from pydantic import BaseModel, Field


class CustomerRqst(BaseModel):
    name: str = Field(min_length=3, max_length=50)
    age: int = Field(ge=18)
    email: str


class CustomerRsps(BaseModel):
    id: uuid.UUID
    name: str
    age: int
    email: str
