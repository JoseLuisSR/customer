from __future__ import annotations

from abc import ABC, abstractmethod

from customers.domain.entities.customer import Customer


class CustomerRepository(ABC):
    """Puerto de salida para la persistencia de clientes.

    La capa de aplicación depende únicamente de esta abstracción (DIP);
    la implementación concreta vive en `infrastructure/persistence`.
    """

    @abstractmethod
    def add(self, customer: Customer) -> Customer:
        """Persiste un cliente nuevo y devuelve la instancia con `id`
        asignado. Lanza `CustomerEmailAlreadyExistsError` si el email ya
        está registrado."""

    @abstractmethod
    def get_by_id(
        self, customer_id: int, *, include_deleted: bool = False
    ) -> Customer | None:
        """Devuelve el cliente con `customer_id`, o `None` si no existe.
        Por defecto excluye los clientes con soft delete; con
        `include_deleted=True` los incluye (usado por DELETE para
        distinguir "no existe" de "ya eliminado")."""

    @abstractmethod
    def list_active(self) -> list[Customer]:
        """Devuelve todos los clientes sin soft delete."""

    @abstractmethod
    def update(self, customer: Customer) -> Customer:
        """Persiste los cambios de un cliente existente. Lanza
        `CustomerEmailAlreadyExistsError` si el nuevo email ya pertenece a
        otro cliente."""

    @abstractmethod
    def soft_delete(self, customer: Customer) -> Customer:
        """Persiste el estado de `customer` tras haber sido marcado como
        eliminado por el dominio (`customer.deleted_at` ya seteado)."""
