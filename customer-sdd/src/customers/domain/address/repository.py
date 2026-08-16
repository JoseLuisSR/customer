"""Puerto de persistencia (hexagonal) para la entidad `Address`.

La implementación concreta (adaptador SQLAlchemy) llega en la Fase 3
(`infrastructure/persistence/address_repository.py`).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from customers.domain.address.entities import Address
from customers.domain.address.value_objects import AddressId
from customers.domain.customer.value_objects import CustomerId


class AddressRepository(ABC):
    """Puerto de persistencia para `Address`.

    Salvo que se indique lo contrario, las operaciones de lectura excluyen
    por defecto las direcciones con `status = DELETED` (se comportan como
    "no encontradas", ver `specs/customers/plan.md` §1.1).
    """

    @abstractmethod
    def add(self, address: Address) -> None:
        """Persiste una dirección nueva."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, address_id: AddressId) -> Address | None:
        """Obtiene una dirección `ACTIVE` por id, o `None` si no existe."""
        raise NotImplementedError

    @abstractmethod
    def list_by_customer(
        self, customer_id: CustomerId, *, include_deleted: bool = False
    ) -> list[Address]:
        """Lista las direcciones de un cliente.

        Por defecto (`include_deleted=False`) solo devuelve direcciones
        `ACTIVE`.
        """
        raise NotImplementedError

    @abstractmethod
    def count_active_by_customer(self, customer_id: CustomerId) -> int:
        """Cuenta las direcciones `ACTIVE` de un cliente (soporta RN-003)."""
        raise NotImplementedError

    @abstractmethod
    def update(self, address: Address) -> None:
        """Persiste cambios sobre una dirección existente (incluye soft delete)."""
        raise NotImplementedError

    @abstractmethod
    def mark_all_deleted_by_customer(self, customer_id: CustomerId) -> None:
        """Marca `DELETED` todas las direcciones `ACTIVE` de un cliente.

        Usado por `DeleteCustomer` (Fase 2) para garantizar que no queden
        direcciones huérfanas en estado `ACTIVE` tras eliminar el cliente
        (RN-004).
        """
        raise NotImplementedError
