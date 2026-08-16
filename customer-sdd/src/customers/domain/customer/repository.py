"""Puerto de persistencia (hexagonal) para el agregado `Customer`.

La implementación concreta (adaptador SQLAlchemy) llega en la Fase 3
(`infrastructure/persistence/customer_repository.py`). Este puerto ya
incluye `get_by_id_for_update`, aunque su implementación real con
`SELECT ... FOR UPDATE` no exista todavía, para no tener que ampliar el
contrato más adelante (`specs/customers/plan.md` §1.4).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from customers.domain.customer.entities import Customer
from customers.domain.customer.value_objects import CustomerId, Email, Identification


class CustomerRepository(ABC):
    """Puerto de persistencia para `Customer`.

    Salvo que se indique lo contrario, las operaciones de lectura excluyen
    por defecto los clientes con `status = DELETED` (se comportan como "no
    encontrados", ver `specs/customers/plan.md` §1.1).
    """

    @abstractmethod
    def add(self, customer: Customer) -> None:
        """Persiste un cliente nuevo."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, customer_id: CustomerId) -> Customer | None:
        """Obtiene un cliente `ACTIVE` por id, o `None` si no existe."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id_for_update(self, customer_id: CustomerId) -> Customer | None:
        """Obtiene un cliente `ACTIVE` por id aplicando bloqueo pesimista.

        Equivalente a `get_by_id`, pero adquiere un `SELECT ... FOR UPDATE`
        sobre la fila del cliente. Lo usa `CreateAddress` (Fase 2) antes de
        contar direcciones activas e insertar, para evitar condiciones de
        carrera entre altas simultáneas que individualmente pasarían la
        validación de dominio pero en conjunto superarían el límite de
        cinco direcciones (RN-003, `specs/customers/plan.md` §1.4).
        """
        raise NotImplementedError

    @abstractmethod
    def list_paginated(self, page: int, page_size: int) -> tuple[list[Customer], int]:
        """Lista clientes `ACTIVE` paginados.

        Returns:
            Tupla `(clientes de la página solicitada, total de clientes
            ACTIVE)`.
        """
        raise NotImplementedError

    @abstractmethod
    def find_by_email(
        self, email: Email, *, exclude_customer_id: CustomerId | None = None
    ) -> Customer | None:
        """Busca un cliente `ACTIVE` por `email` normalizado.

        `exclude_customer_id` permite excluir al propio cliente de la
        búsqueda al actualizar (evita un falso `DuplicateEmailError` cuando
        el cliente reenvía su propio correo sin cambios, spec §16).
        """
        raise NotImplementedError

    @abstractmethod
    def find_by_identification(
        self, identification: Identification, *, exclude_customer_id: CustomerId | None = None
    ) -> Customer | None:
        """Busca un cliente `ACTIVE` por `identification` normalizada.

        Análogo a `find_by_email`, ver `exclude_customer_id`.
        """
        raise NotImplementedError

    @abstractmethod
    def update(self, customer: Customer) -> None:
        """Persiste cambios sobre un cliente existente (incluye soft delete)."""
        raise NotImplementedError
