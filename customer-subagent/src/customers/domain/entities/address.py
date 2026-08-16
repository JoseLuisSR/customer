from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from customers.domain.exceptions import (
    AddressAlreadyDeletedError,
    AddressValidationError,
)

MAX_COUNTRY_LENGTH = 100
MAX_STATE_LENGTH = 100
MAX_CITY_LENGTH = 100
MAX_POSTAL_CODE_LENGTH = 20
MAX_ADDRESS_LINE_LENGTH = 255


@dataclass
class Address:
    """Entidad de dominio Address. No conoce Flask ni SQLAlchemy."""

    customer_id: int
    country: str
    state: str
    city: str
    postal_code: str
    address_line: str
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

    def __post_init__(self) -> None:
        self.customer_id = self._validate_customer_id(self.customer_id)
        self.country = self._validate_text(self.country, "country", MAX_COUNTRY_LENGTH)
        self.state = self._validate_text(self.state, "state", MAX_STATE_LENGTH)
        self.city = self._validate_text(self.city, "city", MAX_CITY_LENGTH)
        self.postal_code = self._validate_text(
            self.postal_code, "postal_code", MAX_POSTAL_CODE_LENGTH
        )
        self.address_line = self._validate_text(
            self.address_line, "address_line", MAX_ADDRESS_LINE_LENGTH
        )

    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def update_country(self, country: str) -> None:
        self.country = self._validate_text(country, "country", MAX_COUNTRY_LENGTH)

    def update_state(self, state: str) -> None:
        self.state = self._validate_text(state, "state", MAX_STATE_LENGTH)

    def update_city(self, city: str) -> None:
        self.city = self._validate_text(city, "city", MAX_CITY_LENGTH)

    def update_postal_code(self, postal_code: str) -> None:
        self.postal_code = self._validate_text(
            postal_code, "postal_code", MAX_POSTAL_CODE_LENGTH
        )

    def update_address_line(self, address_line: str) -> None:
        self.address_line = self._validate_text(
            address_line, "address_line", MAX_ADDRESS_LINE_LENGTH
        )

    def mark_deleted(self, deleted_at: datetime) -> None:
        if self.is_deleted():
            raise AddressAlreadyDeletedError(self.id)
        self.deleted_at = deleted_at

    @staticmethod
    def _validate_customer_id(customer_id: int) -> int:
        if isinstance(customer_id, bool) or not isinstance(customer_id, int):
            raise AddressValidationError("customer_id", "must be an integer")
        if customer_id <= 0:
            raise AddressValidationError("customer_id", "must be a positive integer")
        return customer_id

    @staticmethod
    def _validate_text(value: str, field: str, max_length: int) -> str:
        if not isinstance(value, str):
            raise AddressValidationError(field, "must be a string")
        stripped = value.strip()
        if not stripped:
            raise AddressValidationError(field, "must not be empty")
        if len(stripped) > max_length:
            raise AddressValidationError(
                field, f"must be at most {max_length} characters"
            )
        return stripped
