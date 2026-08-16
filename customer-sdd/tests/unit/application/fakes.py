"""Repositorios *fake* en memoria para pruebas unitarias de aplicación.

No usan SQL ni ningún adaptador real; sirven únicamente para probar los
casos de uso de `application/*` de forma aislada, siguiendo
`specs/customers/implementation-plan.md` §7.1. `get_by_id_for_update`
simplemente delega en `get_by_id`: no hay concurrencia real en memoria (la
concurrencia real se prueba en la Fase 6, con Postgres).
"""

from __future__ import annotations

from datetime import UTC, datetime

from customers.domain.address.entities import Address
from customers.domain.address.repository import AddressRepository
from customers.domain.address.value_objects import AddressId
from customers.domain.customer.entities import Customer
from customers.domain.customer.repository import CustomerRepository
from customers.domain.customer.value_objects import CustomerId, Email, Identification
from customers.domain.shared.status import EntityStatus


class FakeCustomerRepository(CustomerRepository):
    """Implementación en memoria de `CustomerRepository` para pruebas."""

    def __init__(self) -> None:
        self._customers: dict[str, Customer] = {}

    def add(self, customer: Customer) -> None:
        # Simula el `server_default=now()` de Postgres (Fase 3): los
        # adaptadores reales fijan `created_at`/`updated_at` en el propio
        # objeto de dominio tras el `flush()` (ver
        # `SqlAlchemyCustomerRepository.add`); este fake replica ese
        # comportamiento para poder cubrir la regresión sin Postgres.
        now = datetime.now(UTC)
        customer.created_at = now
        customer.updated_at = now
        self._customers[str(customer.id)] = customer

    def get_by_id(self, customer_id: CustomerId) -> Customer | None:
        customer = self._customers.get(str(customer_id))
        if customer is None or customer.status is EntityStatus.DELETED:
            return None
        return customer

    def get_by_id_for_update(self, customer_id: CustomerId) -> Customer | None:
        return self.get_by_id(customer_id)

    def list_paginated(self, page: int, page_size: int) -> tuple[list[Customer], int]:
        active = [
            customer
            for customer in self._customers.values()
            if customer.status is EntityStatus.ACTIVE
        ]
        active.sort(key=lambda customer: str(customer.id))
        total = len(active)
        start = (page - 1) * page_size
        end = start + page_size
        return active[start:end], total

    def find_by_email(
        self, email: Email, *, exclude_customer_id: CustomerId | None = None
    ) -> Customer | None:
        for customer in self._customers.values():
            if customer.status is not EntityStatus.ACTIVE:
                continue
            if exclude_customer_id is not None and customer.id == exclude_customer_id:
                continue
            if customer.email.value == email.value:
                return customer
        return None

    def find_by_identification(
        self, identification: Identification, *, exclude_customer_id: CustomerId | None = None
    ) -> Customer | None:
        for customer in self._customers.values():
            if customer.status is not EntityStatus.ACTIVE:
                continue
            if exclude_customer_id is not None and customer.id == exclude_customer_id:
                continue
            if customer.identification.value == identification.value:
                return customer
        return None

    def update(self, customer: Customer) -> None:
        self._customers[str(customer.id)] = customer

    def all(self) -> list[Customer]:
        """Devuelve todos los clientes almacenados (incluye `DELETED`).

        Solo para aserciones de prueba, no forma parte del puerto.
        """
        return list(self._customers.values())


class FakeAddressRepository(AddressRepository):
    """Implementación en memoria de `AddressRepository` para pruebas."""

    def __init__(self) -> None:
        self._addresses: dict[str, Address] = {}

    def add(self, address: Address) -> None:
        # Ver comentario equivalente en `FakeCustomerRepository.add`.
        now = datetime.now(UTC)
        address.created_at = now
        address.updated_at = now
        self._addresses[str(address.id)] = address

    def get_by_id(self, address_id: AddressId) -> Address | None:
        address = self._addresses.get(str(address_id))
        if address is None or address.status is EntityStatus.DELETED:
            return None
        return address

    def list_by_customer(
        self, customer_id: CustomerId, *, include_deleted: bool = False
    ) -> list[Address]:
        return [
            address
            for address in self._addresses.values()
            if address.customer_id == customer_id
            and (include_deleted or address.status is EntityStatus.ACTIVE)
        ]

    def count_active_by_customer(self, customer_id: CustomerId) -> int:
        return len(self.list_by_customer(customer_id))

    def update(self, address: Address) -> None:
        self._addresses[str(address.id)] = address

    def mark_all_deleted_by_customer(self, customer_id: CustomerId) -> None:
        for address in self._addresses.values():
            if address.customer_id == customer_id and address.status is EntityStatus.ACTIVE:
                address.mark_deleted()

    def all(self) -> list[Address]:
        """Devuelve todas las direcciones almacenadas (incluye `DELETED`).

        Solo para aserciones de prueba, no forma parte del puerto.
        """
        return list(self._addresses.values())
