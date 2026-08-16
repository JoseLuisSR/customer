from __future__ import annotations

from dataclasses import dataclass

from customers.domain.entities.address import Address


@dataclass(frozen=True)
class CreateAddressInput:
    customer_id: int
    country: str
    state: str
    city: str
    postal_code: str
    address_line: str


@dataclass(frozen=True)
class UpdateAddressInput:
    customer_id: int
    address_id: int
    country: str | None = None
    state: str | None = None
    city: str | None = None
    postal_code: str | None = None
    address_line: str | None = None
    body_id: int | None = None
    """Id opcional recibido en el body de la request (si el cliente lo
    envía), usado para validar que coincide con el id de la dirección en
    la URL."""


@dataclass(frozen=True)
class AddressOutput:
    id: int
    country: str
    state: str
    city: str
    postal_code: str
    address_line: str

    @classmethod
    def from_entity(cls, address: Address) -> AddressOutput:
        return cls(
            id=address.id,
            country=address.country,
            state=address.state,
            city=address.city,
            postal_code=address.postal_code,
            address_line=address.address_line,
        )
