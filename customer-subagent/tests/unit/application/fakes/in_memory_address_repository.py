from __future__ import annotations

import copy
from datetime import UTC, datetime

from customers.domain.entities.address import Address
from customers.domain.repositories.address_repository import AddressRepository


class InMemoryAddressRepository(AddressRepository):
    """Doble de prueba del puerto AddressRepository, usado por los tests
    de casos de uso para evitar depender de infraestructura real (LSP).
    Filtra siempre por `customer_id`, igual que hará el adaptador
    SQLAlchemy, para poder testear el aislamiento entre customers."""

    def __init__(self) -> None:
        self._addresses: dict[int, Address] = {}
        self._next_id = 1

    def add(self, address: Address) -> Address:
        stored = copy.deepcopy(address)
        stored.id = self._next_id
        self._next_id += 1
        now = datetime.now(UTC)
        stored.created_at = now
        stored.updated_at = now
        self._addresses[stored.id] = stored
        return copy.deepcopy(stored)

    def get_by_id(
        self, customer_id: int, address_id: int, *, include_deleted: bool = False
    ) -> Address | None:
        address = self._addresses.get(address_id)
        if address is None or address.customer_id != customer_id:
            return None
        if address.is_deleted() and not include_deleted:
            return None
        return copy.deepcopy(address)

    def list_active_by_customer(self, customer_id: int) -> list[Address]:
        return [
            copy.deepcopy(address)
            for address in self._addresses.values()
            if address.customer_id == customer_id and not address.is_deleted()
        ]

    def update(self, address: Address) -> Address:
        stored = copy.deepcopy(address)
        stored.updated_at = datetime.now(UTC)
        self._addresses[stored.id] = stored
        return copy.deepcopy(stored)

    def soft_delete(self, address: Address) -> Address:
        stored = copy.deepcopy(address)
        stored.updated_at = datetime.now(UTC)
        self._addresses[stored.id] = stored
        return copy.deepcopy(stored)
