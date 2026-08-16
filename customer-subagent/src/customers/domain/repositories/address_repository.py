from __future__ import annotations

from abc import ABC, abstractmethod

from customers.domain.entities.address import Address


class AddressRepository(ABC):
    """Puerto de salida para la persistencia de direcciones.

    Las operaciones de lectura exigen `customer_id` para garantizar que una
    dirección de un cliente nunca sea visible ni editable a través del
    `customer_id` de otro (aislamiento del recurso anidado). La capa de
    aplicación depende únicamente de esta abstracción (DIP); la
    implementación concreta vive en `infrastructure/persistence`.
    """

    @abstractmethod
    def add(self, address: Address) -> Address:
        """Persiste una dirección nueva (con `address.customer_id` ya
        asignado) y devuelve la instancia con `id` asignado."""

    @abstractmethod
    def get_by_id(
        self, customer_id: int, address_id: int, *, include_deleted: bool = False
    ) -> Address | None:
        """Devuelve la dirección `address_id` perteneciente a
        `customer_id`, o `None` si no existe o pertenece a otro cliente.
        Por defecto excluye las direcciones con soft delete; con
        `include_deleted=True` las incluye (usado por DELETE para
        distinguir "no existe" de "ya eliminada")."""

    @abstractmethod
    def list_active_by_customer(self, customer_id: int) -> list[Address]:
        """Devuelve todas las direcciones activas (sin soft delete) del
        cliente `customer_id`."""

    @abstractmethod
    def update(self, address: Address) -> Address:
        """Persiste los cambios de una dirección existente."""

    @abstractmethod
    def soft_delete(self, address: Address) -> Address:
        """Persiste el estado de `address` tras haber sido marcada como
        eliminada por el dominio (`address.deleted_at` ya seteado)."""
