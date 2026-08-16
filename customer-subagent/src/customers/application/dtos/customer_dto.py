from __future__ import annotations

from dataclasses import dataclass

from customers.domain.entities.customer import Customer


@dataclass(frozen=True)
class CreateCustomerInput:
    name: str
    age: int
    email: str


@dataclass(frozen=True)
class UpdateCustomerInput:
    customer_id: int
    name: str | None = None
    age: int | None = None
    email: str | None = None
    body_id: int | None = None
    """Id opcional recibido en el body de la request (si el cliente lo
    envía), usado para validar que coincide con el id de la URL."""


@dataclass(frozen=True)
class CustomerOutput:
    id: int
    name: str
    age: int
    email: str

    @classmethod
    def from_entity(cls, customer: Customer) -> CustomerOutput:
        return cls(
            id=customer.id,
            name=customer.name,
            age=customer.age,
            email=customer.email,
        )
