"""Value objects de la entidad `Address`.

Todos los campos de texto comparten la misma validación funcional
(VAL-009: no deben estar vacíos tras `trim`), incluyendo `postal_code` sin
excepción por país (Q-005, `specs/customers/plan.md` §7.5). Cada uno
expone, además del constructor (lanza `InvalidAddressFieldError`), un
método de clase `validate(raw_value) -> FieldError | None` que no lanza
excepción, para que la capa de aplicación pueda acumular un error por cada
campo inválido de una misma dirección (`specs/customers/plan.md` §2.5,
ver también `specs/customers/implementation-plan.md` §3.2).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from customers.domain.address.exceptions import InvalidAddressFieldError
from customers.domain.shared.validation import FieldError, require_non_blank

_VAL_CODE = "VAL-009"


@dataclass(frozen=True, slots=True, init=False)
class Country:
    """País de la dirección."""

    value: str

    def __init__(self, raw_value: str) -> None:
        normalized, error = self.validate_raw(raw_value)
        if error is not None:
            raise InvalidAddressFieldError(error.message)
        object.__setattr__(self, "value", normalized)

    @staticmethod
    def validate_raw(raw_value: str) -> tuple[str, FieldError | None]:
        return require_non_blank(
            raw_value, code=_VAL_CODE, field="country", message="El país no debe estar vacío."
        )

    @classmethod
    def validate(cls, raw_value: str) -> FieldError | None:
        _, error = cls.validate_raw(raw_value)
        return error

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, init=False)
class State:
    """Estado, departamento o provincia de la dirección."""

    value: str

    def __init__(self, raw_value: str) -> None:
        normalized, error = self.validate_raw(raw_value)
        if error is not None:
            raise InvalidAddressFieldError(error.message)
        object.__setattr__(self, "value", normalized)

    @staticmethod
    def validate_raw(raw_value: str) -> tuple[str, FieldError | None]:
        return require_non_blank(
            raw_value,
            code=_VAL_CODE,
            field="state",
            message="El estado, departamento o provincia no debe estar vacío.",
        )

    @classmethod
    def validate(cls, raw_value: str) -> FieldError | None:
        _, error = cls.validate_raw(raw_value)
        return error

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, init=False)
class City:
    """Ciudad de la dirección."""

    value: str

    def __init__(self, raw_value: str) -> None:
        normalized, error = self.validate_raw(raw_value)
        if error is not None:
            raise InvalidAddressFieldError(error.message)
        object.__setattr__(self, "value", normalized)

    @staticmethod
    def validate_raw(raw_value: str) -> tuple[str, FieldError | None]:
        return require_non_blank(
            raw_value, code=_VAL_CODE, field="city", message="La ciudad no debe estar vacía."
        )

    @classmethod
    def validate(cls, raw_value: str) -> FieldError | None:
        _, error = cls.validate_raw(raw_value)
        return error

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, init=False)
class StreetAddress:
    """Dirección física (calle/número/complemento).

    Corresponde al campo `address` del contrato JSON (`AddressRequest`/
    `AddressResponse`, `specs/customers/plan.md` §2.3); se nombra
    `StreetAddress` en el dominio para no colisionar con el nombre de la
    entidad `Address`.
    """

    value: str

    def __init__(self, raw_value: str) -> None:
        normalized, error = self.validate_raw(raw_value)
        if error is not None:
            raise InvalidAddressFieldError(error.message)
        object.__setattr__(self, "value", normalized)

    @staticmethod
    def validate_raw(raw_value: str) -> tuple[str, FieldError | None]:
        return require_non_blank(
            raw_value,
            code=_VAL_CODE,
            field="address",
            message="La dirección física no debe estar vacía.",
        )

    @classmethod
    def validate(cls, raw_value: str) -> FieldError | None:
        _, error = cls.validate_raw(raw_value)
        return error

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, init=False)
class PostalCode:
    """Código postal de la dirección.

    Obligatorio para todos los países, sin excepción (Q-005 confirmada
    como supuesto de ingeniería, `specs/customers/plan.md` §7.5).
    """

    value: str

    def __init__(self, raw_value: str) -> None:
        normalized, error = self.validate_raw(raw_value)
        if error is not None:
            raise InvalidAddressFieldError(error.message)
        object.__setattr__(self, "value", normalized)

    @staticmethod
    def validate_raw(raw_value: str) -> tuple[str, FieldError | None]:
        return require_non_blank(
            raw_value,
            code=_VAL_CODE,
            field="postal_code",
            message="El código postal no debe estar vacío.",
        )

    @classmethod
    def validate(cls, raw_value: str) -> FieldError | None:
        _, error = cls.validate_raw(raw_value)
        return error

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, init=False)
class AddressId:
    """Identificador único de la dirección (`UUID` v4, generado en dominio)."""

    value: uuid.UUID

    def __init__(self, value: uuid.UUID) -> None:
        object.__setattr__(self, "value", value)

    @classmethod
    def generate(cls) -> AddressId:
        """Genera un nuevo identificador `UUID` v4."""
        return cls(uuid.uuid4())

    @classmethod
    def from_string(cls, raw_value: str) -> AddressId:
        """Construye un `AddressId` a partir de su representación textual.

        Lanza `ValueError` si `raw_value` no es un `UUID` válido.
        """
        try:
            return cls(uuid.UUID(str(raw_value)))
        except (ValueError, AttributeError, TypeError) as exc:
            raise ValueError(f"'{raw_value}' no es un identificador de dirección válido.") from exc

    def __str__(self) -> str:
        return str(self.value)
