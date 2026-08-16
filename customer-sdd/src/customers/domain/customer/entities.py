"""Entidad agregado `Customer`."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar

from customers.domain.address.entities import Address
from customers.domain.address.exceptions import AddressCustomerMismatchError
from customers.domain.customer.exceptions import MaxAddressesExceededError
from customers.domain.customer.value_objects import Age, CustomerId, Email, Identification, Name
from customers.domain.shared.status import EntityStatus


@dataclass(slots=True)
class Customer:
    """Agregado raíz `Customer`.

    Es responsable de mantener sus propios invariantes de negocio:
    - Máximo cinco direcciones activas (RN-003), aplicado en `add_address`.
    - Al eliminarse, ninguna dirección propia queda `ACTIVE` (RN-004),
      aplicado en `mark_deleted`.
    """

    id: CustomerId
    name: Name
    identification: Identification
    age: Age
    email: Email
    status: EntityStatus
    addresses: list[Address] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    MAX_ACTIVE_ADDRESSES: ClassVar[int] = 5

    @classmethod
    def create(
        cls,
        *,
        name: Name,
        identification: Identification,
        age: Age,
        email: Email,
        customer_id: CustomerId | None = None,
    ) -> Customer:
        """Construye un cliente nuevo, `ACTIVE` y sin direcciones."""
        return cls(
            id=customer_id or CustomerId.generate(),
            name=name,
            identification=identification,
            age=age,
            email=email,
            status=EntityStatus.ACTIVE,
            addresses=[],
        )

    def active_addresses(self) -> list[Address]:
        """Direcciones actualmente `ACTIVE` de este cliente."""
        return [address for address in self.addresses if address.status is EntityStatus.ACTIVE]

    def add_address(self, address: Address) -> None:
        """Agrega `address` a la colección del cliente.

        Lanza:
            AddressCustomerMismatchError: si `address.customer_id` no
                coincide con el id de este cliente (VAL-008/ERR-006).
            MaxAddressesExceededError: si el cliente ya tiene cinco
                direcciones `ACTIVE` (RN-003/VAL-007).
        """
        if address.customer_id != self.id:
            raise AddressCustomerMismatchError(address_id=address.id, customer_id=self.id)
        if len(self.active_addresses()) >= self.MAX_ACTIVE_ADDRESSES:
            raise MaxAddressesExceededError(customer_id=self.id)
        self.addresses.append(address)

    def mark_deleted(self) -> None:
        """Marca el cliente como `DELETED` (RN-004).

        También marca `DELETED` cada dirección propia que siga `ACTIVE`,
        de modo que no queden direcciones huérfanas en estado activo tras
        eliminar el cliente. Es un borrado lógico (Q-004): no elimina
        físicamente ninguna fila.
        """
        self.status = EntityStatus.DELETED
        for address in self.addresses:
            if address.status is EntityStatus.ACTIVE:
                address.mark_deleted()
