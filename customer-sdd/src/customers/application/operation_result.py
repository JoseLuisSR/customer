"""DTO del sobre de resultado funcional (RN-006).

Todos los casos de uso de la capa de aplicación devuelven una instancia de
`OperationResult`, tanto en el camino de éxito como en el de fallo. Ninguna
excepción de dominio se propaga fuera de esta capa sin ser traducida a este
sobre (ver `specs/customers/implementation-plan.md` §4.3, CA-008).

La estructura replica el contrato `specs/customers/plan.md` §2.1; la capa
HTTP (Fase 4) solo necesita serializar esta instancia a JSON, sin volver a
decidir campos de negocio.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from customers.domain.shared.status import EntityStatus
from customers.domain.shared.validation import FieldError


class Operation(StrEnum):
    """Tipo de operación ejecutada (`plan.md` §2.1)."""

    CREATE = "create"
    READ = "read"
    LIST = "list"
    UPDATE = "update"
    DELETE = "delete"


class Entity(StrEnum):
    """Tipo de entidad afectada por la operación (`plan.md` §2.1)."""

    CUSTOMER = "customer"
    ADDRESS = "address"


@dataclass(frozen=True, slots=True)
class OperationResult:
    """Sobre de resultado funcional devuelto por todos los casos de uso.

    Attributes:
        success: `True` si la operación se completó según lo solicitado.
        operation: Tipo de operación (`create`, `read`, `list`, `update`,
            `delete`).
        entity: Entidad principal afectada (`customer`/`address`).
        entity_status: Estado de la entidad tras la operación, o `None`
            cuando no aplica a una única entidad (listados) o la operación
            fue rechazada antes de identificar una entidad concreta.
        message: Mensaje descriptivo apto para el consumidor de la API.
        data: Datos de la operación exitosa (representación de la entidad
            o de un listado). `None` en resultados fallidos.
        errors: Lista de errores funcionales de una operación fallida.
            `None` en resultados exitosos.
    """

    success: bool
    operation: Operation
    entity: Entity
    entity_status: EntityStatus | None
    message: str
    data: dict[str, Any] | None = None
    errors: list[FieldError] | None = None

    @classmethod
    def ok(
        cls,
        *,
        operation: Operation,
        entity: Entity,
        entity_status: EntityStatus | None,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> OperationResult:
        """Construye un resultado exitoso (`success=True`, `errors=None`)."""
        return cls(
            success=True,
            operation=operation,
            entity=entity,
            entity_status=entity_status,
            message=message,
            data=data,
            errors=None,
        )

    @classmethod
    def fail(
        cls,
        *,
        operation: Operation,
        entity: Entity,
        message: str,
        errors: list[FieldError],
        entity_status: EntityStatus | None = None,
    ) -> OperationResult:
        """Construye un resultado fallido (`success=False`, `data=None`)."""
        return cls(
            success=False,
            operation=operation,
            entity=entity,
            entity_status=entity_status,
            message=message,
            data=None,
            errors=errors,
        )
