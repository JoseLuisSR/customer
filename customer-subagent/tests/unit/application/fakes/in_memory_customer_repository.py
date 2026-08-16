from __future__ import annotations

import copy
from datetime import UTC, datetime

from customers.domain.entities.customer import Customer
from customers.domain.exceptions import CustomerEmailAlreadyExistsError
from customers.domain.repositories.customer_repository import CustomerRepository


class InMemoryCustomerRepository(CustomerRepository):
    """Doble de prueba del puerto CustomerRepository, usado por los tests
    de casos de uso para evitar depender de infraestructura real (LSP)."""

    def __init__(self) -> None:
        self._customers: dict[int, Customer] = {}
        self._next_id = 1

    def add(self, customer: Customer) -> Customer:
        self._raise_if_email_taken(customer.email)
        stored = copy.deepcopy(customer)
        stored.id = self._next_id
        self._next_id += 1
        now = datetime.now(UTC)
        stored.created_at = now
        stored.updated_at = now
        self._customers[stored.id] = stored
        return copy.deepcopy(stored)

    def get_by_id(
        self, customer_id: int, *, include_deleted: bool = False
    ) -> Customer | None:
        customer = self._customers.get(customer_id)
        if customer is None:
            return None
        if customer.is_deleted() and not include_deleted:
            return None
        return copy.deepcopy(customer)

    def list_active(self) -> list[Customer]:
        return [
            copy.deepcopy(customer)
            for customer in self._customers.values()
            if not customer.is_deleted()
        ]

    def update(self, customer: Customer) -> Customer:
        self._raise_if_email_taken(customer.email, exclude_id=customer.id)
        stored = copy.deepcopy(customer)
        stored.updated_at = datetime.now(UTC)
        self._customers[stored.id] = stored
        return copy.deepcopy(stored)

    def soft_delete(self, customer: Customer) -> Customer:
        stored = copy.deepcopy(customer)
        stored.updated_at = datetime.now(UTC)
        self._customers[stored.id] = stored
        return copy.deepcopy(stored)

    def _raise_if_email_taken(
        self, email: str, *, exclude_id: int | None = None
    ) -> None:
        for existing in self._customers.values():
            if existing.email == email and existing.id != exclude_id:
                raise CustomerEmailAlreadyExistsError(email)
