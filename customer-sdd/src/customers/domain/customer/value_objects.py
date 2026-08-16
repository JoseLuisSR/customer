"""Value objects del agregado `Customer`.

Cada value object expone dos formas de validación (ver
`specs/customers/implementation-plan.md` §3.2):

- El constructor (``__init__``), que normaliza y **lanza** la excepción de
  dominio correspondiente si el valor no es válido. Se usa para construir
  entidades una vez que se sabe que todos los campos son válidos.
- El método de clase ``validate(raw_value) -> FieldError | None``, que
  realiza la misma validación **sin lanzar** ninguna excepción. Permite a
  la capa de aplicación validar varios campos de un mismo payload y
  acumular todos los errores encontrados antes de decidir si rechaza la
  operación (requerido explícitamente para direcciones con varios campos
  vacíos, `specs/customers/plan.md` §2.5, pero implementado de forma
  consistente en todos los value objects para reutilizar el mismo
  mecanismo en `infrastructure/http/schemas.py`, Fase 4).
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass

from customers.domain.customer.exceptions import (
    InvalidAgeError,
    InvalidEmailError,
    InvalidIdentificationError,
    InvalidNameError,
)
from customers.domain.shared.validation import FieldError, require_non_blank

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_MIN_AGE = 0
_MAX_AGE = 120


@dataclass(frozen=True, slots=True, init=False)
class Email:
    """Correo electrónico del cliente (VAL-001).

    Normaliza `trim` + `lower` en la construcción: se persiste un único
    valor normalizado, no se conserva el casing original del usuario
    (resuelve el caso límite "correo con mayúsculas/minúsculas o espacios",
    spec §16). La unicidad (VAL-002) se valida en la capa de aplicación,
    no aquí.
    """

    value: str

    def __init__(self, raw_value: str) -> None:
        normalized, error = self.validate_raw(raw_value)
        if error is not None:
            raise InvalidEmailError(error.message)
        object.__setattr__(self, "value", normalized)

    @staticmethod
    def validate_raw(raw_value: str) -> tuple[str, FieldError | None]:
        normalized = raw_value.strip().lower()
        if not _EMAIL_PATTERN.match(normalized):
            return normalized, FieldError(
                code="VAL-001",
                field="email",
                message="El correo electrónico debe tener un formato válido.",
            )
        return normalized, None

    @classmethod
    def validate(cls, raw_value: str) -> FieldError | None:
        _, error = cls.validate_raw(raw_value)
        return error

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, init=False)
class Name:
    """Nombre del cliente (VAL-003: no debe estar vacío tras `trim`)."""

    value: str

    def __init__(self, raw_value: str) -> None:
        normalized, error = self.validate_raw(raw_value)
        if error is not None:
            raise InvalidNameError(error.message)
        object.__setattr__(self, "value", normalized)

    @staticmethod
    def validate_raw(raw_value: str) -> tuple[str, FieldError | None]:
        return require_non_blank(
            raw_value, code="VAL-003", field="name", message="El nombre no debe estar vacío."
        )

    @classmethod
    def validate(cls, raw_value: str) -> FieldError | None:
        _, error = cls.validate_raw(raw_value)
        return error

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, init=False)
class Identification:
    """Identificación del cliente (VAL-004: no debe estar vacía tras `trim`).

    Decisión de negocio Q-001 confirmada el 2026-07-25 (ver
    `specs/customers/plan.md` §1.1/§7.1): `identification` debe ser única,
    igual que `email`. A diferencia de `Email`, este value object **solo**
    normaliza `trim` — deliberadamente **no** aplica `lower()`. El spec
    funcional no define un caso límite de comparación insensible a
    mayúsculas/minúsculas para este campo (sí lo hace explícitamente para
    el correo, spec §16), y muchos documentos de identificación reales son
    alfanuméricos donde el casing puede ser significativo. Si negocio
    confirma en el futuro que también debe normalizarse con `lower()`, el
    cambio se limita a este value object, sin migración de esquema.
    """

    value: str

    def __init__(self, raw_value: str) -> None:
        normalized, error = self.validate_raw(raw_value)
        if error is not None:
            raise InvalidIdentificationError(error.message)
        object.__setattr__(self, "value", normalized)

    @staticmethod
    def validate_raw(raw_value: str) -> tuple[str, FieldError | None]:
        return require_non_blank(
            raw_value,
            code="VAL-004",
            field="identification",
            message="La identificación no debe estar vacía.",
        )

    @classmethod
    def validate(cls, raw_value: str) -> FieldError | None:
        _, error = cls.validate_raw(raw_value)
        return error

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, init=False)
class Age:
    """Edad del cliente (VAL-005: entero entre 0 y 120).

    El límite inferior (`>= 0`) proviene explícitamente del spec funcional;
    el límite superior (`<= 120`) es una cota de sanidad técnica (Q-002,
    `specs/customers/plan.md` §7.2), pendiente de confirmación por negocio.
    """

    value: int

    def __init__(self, raw_value: int) -> None:
        normalized, error = self.validate_raw(raw_value)
        if error is not None:
            raise InvalidAgeError(error.message)
        object.__setattr__(self, "value", normalized)

    @staticmethod
    def validate_raw(raw_value: int) -> tuple[int, FieldError | None]:
        message = f"La edad debe ser un entero entre {_MIN_AGE} y {_MAX_AGE}."
        if isinstance(raw_value, bool) or not isinstance(raw_value, int):
            return 0, FieldError(code="VAL-005", field="age", message=message)
        if raw_value < _MIN_AGE or raw_value > _MAX_AGE:
            return raw_value, FieldError(code="VAL-005", field="age", message=message)
        return raw_value, None

    @classmethod
    def validate(cls, raw_value: int) -> FieldError | None:
        _, error = cls.validate_raw(raw_value)
        return error

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True, slots=True, init=False)
class CustomerId:
    """Identificador único del cliente (`UUID` v4, generado en dominio)."""

    value: uuid.UUID

    def __init__(self, value: uuid.UUID) -> None:
        object.__setattr__(self, "value", value)

    @classmethod
    def generate(cls) -> CustomerId:
        """Genera un nuevo identificador `UUID` v4."""
        return cls(uuid.uuid4())

    @classmethod
    def from_string(cls, raw_value: str) -> CustomerId:
        """Construye un `CustomerId` a partir de su representación textual.

        Lanza `ValueError` si `raw_value` no es un `UUID` válido (se trata
        como un error de forma del request, no como una regla de negocio;
        la traducción a `ERR-001` ocurre en la capa HTTP, Fase 4).
        """
        try:
            return cls(uuid.UUID(str(raw_value)))
        except (ValueError, AttributeError, TypeError) as exc:
            raise ValueError(f"'{raw_value}' no es un identificador de cliente válido.") from exc

    def __str__(self) -> str:
        return str(self.value)
