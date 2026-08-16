"""Construcción del sobre de resultado funcional JSON (RN-006, `plan.md` §2.1).

`OperationResult` (capa de aplicación) ya contiene todos los campos del
sobre; esta función solo lo serializa a `dict` JSON-compatible (los `enum`
`Operation`/`Entity`/`EntityStatus` se convierten a su valor de cadena y
los `FieldError` a objetos `{code, field, message}`).
"""

from __future__ import annotations

from typing import Any

from customers.application.operation_result import OperationResult


def build_envelope(result: OperationResult) -> dict[str, Any]:
    """Convierte un `OperationResult` en el sobre JSON exacto de `plan.md` §2.1."""
    return {
        "success": result.success,
        "operation": result.operation.value,
        "entity": result.entity.value,
        "entity_status": (result.entity_status.value if result.entity_status is not None else None),
        "message": result.message,
        "data": result.data,
        "errors": (
            [
                {"code": error.code, "field": error.field, "message": error.message}
                for error in result.errors
            ]
            if result.errors is not None
            else None
        ),
    }
