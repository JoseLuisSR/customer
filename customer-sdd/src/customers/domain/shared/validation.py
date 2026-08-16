"""Mecanismo de validación compartido por los value objects del dominio.

Ver `specs/customers/implementation-plan.md` §3.2 y `specs/customers/plan.md`
§2.5: ante un payload con varios campos inválidos (por ejemplo, una
dirección con varios campos vacíos), la capa de aplicación debe poder
reportar **todos** los campos inválidos en `errors[]`, no solo el primero.

Para lograrlo, cada value object del dominio expone, junto a su
constructor (que sí lanza una excepción de dominio ante un valor
inválido), un método de clase `validate(raw_value) -> FieldError | None`
que realiza la misma validación pero **sin lanzar** ninguna excepción.
La capa de aplicación (Fase 2) puede así invocar `validate` en cada campo
de un payload, acumular los `FieldError` obtenidos y decidir si rechaza
la operación completa con todos los errores encontrados.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FieldError:
    """Error de validación asociado a un único campo de entrada.

    Attributes:
        code: Código funcional de la validación incumplida (p. ej. ``VAL-001``).
        field: Nombre del campo de entrada al que corresponde el error, o
            ``None`` cuando el error no está asociado a un campo concreto.
        message: Mensaje descriptivo apto para exponer al consumidor de la API.
    """

    code: str
    field: str | None
    message: str


def require_non_blank(
    raw_value: str, *, code: str, field: str, message: str
) -> tuple[str, FieldError | None]:
    """Normaliza (`trim`) `raw_value` y valida que no quede vacío.

    Función auxiliar reutilizada por los value objects de tipo cadena que
    comparten la misma regla ("no vacío tras `trim`"), como `Name`,
    `Identification` y los campos de `Address`.

    Returns:
        Una tupla `(valor_normalizado, error)`. `error` es `None` cuando la
        validación pasa.
    """
    normalized = raw_value.strip()
    if not normalized:
        return normalized, FieldError(code=code, field=field, message=message)
    return normalized, None
