"""Caso de uso `ListCustomers` (RF-003).

Paginación simple `page`/`page_size` (Q-006, `specs/customers/plan.md`
§7.6): por defecto `page_size=20`, máximo 100. No embebe `addresses`
(`plan.md` §2.2).
"""

from __future__ import annotations

from dataclasses import dataclass

from customers.application.customer.support import customer_to_dict
from customers.application.operation_result import Entity, Operation, OperationResult
from customers.domain.customer.repository import CustomerRepository

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


@dataclass(frozen=True, slots=True)
class ListCustomersRequest:
    """Parámetros de paginación de `GET /customers`."""

    page: int | None = None
    page_size: int | None = None


class ListCustomers:
    """Lista clientes `ACTIVE` paginados, sin `addresses` embebidas (RF-003)."""

    def __init__(self, customer_repository: CustomerRepository) -> None:
        self._customer_repository = customer_repository

    def execute(self, request: ListCustomersRequest | None = None) -> OperationResult:
        request = request or ListCustomersRequest()
        page = self._normalize_page(request.page)
        page_size = self._normalize_page_size(request.page_size)

        customers, total = self._customer_repository.list_paginated(page, page_size)

        return OperationResult.ok(
            operation=Operation.LIST,
            entity=Entity.CUSTOMER,
            entity_status=None,
            message="Clientes listados exitosamente.",
            data={
                "items": [customer_to_dict(customer) for customer in customers],
                "page": page,
                "page_size": page_size,
                "total": total,
            },
        )

    @staticmethod
    def _normalize_page(page: int | None) -> int:
        if page is None or page < 1:
            return DEFAULT_PAGE
        return page

    @staticmethod
    def _normalize_page_size(page_size: int | None) -> int:
        if page_size is None or page_size < 1:
            return DEFAULT_PAGE_SIZE
        return min(page_size, MAX_PAGE_SIZE)
