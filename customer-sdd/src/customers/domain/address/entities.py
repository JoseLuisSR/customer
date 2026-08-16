"""Entidad `Address`."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from customers.domain.address.exceptions import InvalidAddressFieldError
from customers.domain.address.value_objects import (
    AddressId,
    City,
    Country,
    PostalCode,
    State,
    StreetAddress,
)
from customers.domain.customer.value_objects import CustomerId
from customers.domain.shared.status import EntityStatus


@dataclass(slots=True)
class Address:
    """Dirección asociada a un cliente.

    No puede existir sin un `customer_id` válido (RN-005): toda dirección
    debe estar asociada a un único cliente existente.
    """

    id: AddressId
    customer_id: CustomerId
    country: Country
    state: State
    city: City
    street_address: StreetAddress
    postal_code: PostalCode
    status: EntityStatus
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.customer_id, CustomerId):
            raise InvalidAddressFieldError(
                "Toda dirección debe estar asociada a un cliente existente (RN-005)."
            )

    @classmethod
    def create(
        cls,
        *,
        customer_id: CustomerId,
        country: Country,
        state: State,
        city: City,
        street_address: StreetAddress,
        postal_code: PostalCode,
        address_id: AddressId | None = None,
    ) -> Address:
        """Construye una dirección nueva, `ACTIVE`."""
        return cls(
            id=address_id or AddressId.generate(),
            customer_id=customer_id,
            country=country,
            state=state,
            city=city,
            street_address=street_address,
            postal_code=postal_code,
            status=EntityStatus.ACTIVE,
        )

    def mark_deleted(self) -> None:
        """Marca la dirección como `DELETED` (borrado lógico, Q-004)."""
        self.status = EntityStatus.DELETED
