from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from customers.domain.exceptions import (
    CustomerAlreadyDeletedError,
    CustomerValidationError,
)

MIN_AGE = 0
MAX_AGE = 120
MAX_NAME_LENGTH = 255
MAX_EMAIL_LENGTH = 255

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass
class Customer:
    """Entidad de dominio Customer. No conoce Flask ni SQLAlchemy."""

    name: str
    age: int
    email: str
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

    def __post_init__(self) -> None:
        self.name = self._validate_name(self.name)
        self.age = self._validate_age(self.age)
        self.email = self._validate_email(self.email)

    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def rename(self, name: str) -> None:
        self.name = self._validate_name(name)

    def update_age(self, age: int) -> None:
        self.age = self._validate_age(age)

    def update_email(self, email: str) -> None:
        self.email = self._validate_email(email)

    def mark_deleted(self, deleted_at: datetime) -> None:
        if self.is_deleted():
            raise CustomerAlreadyDeletedError(self.id)
        self.deleted_at = deleted_at

    @staticmethod
    def _validate_name(name: str) -> str:
        if not isinstance(name, str):
            raise CustomerValidationError("name", "must be a string")
        stripped = name.strip()
        if not stripped:
            raise CustomerValidationError("name", "must not be empty")
        if len(stripped) > MAX_NAME_LENGTH:
            raise CustomerValidationError(
                "name", f"must be at most {MAX_NAME_LENGTH} characters"
            )
        return stripped

    @staticmethod
    def _validate_age(age: int) -> int:
        if isinstance(age, bool) or not isinstance(age, int):
            raise CustomerValidationError("age", "must be an integer")
        if age < MIN_AGE or age > MAX_AGE:
            raise CustomerValidationError(
                "age", f"must be between {MIN_AGE} and {MAX_AGE}"
            )
        return age

    @staticmethod
    def _validate_email(email: str) -> str:
        if not isinstance(email, str):
            raise CustomerValidationError("email", "must be a string")
        stripped = email.strip()
        if not stripped:
            raise CustomerValidationError("email", "must not be empty")
        if len(stripped) > MAX_EMAIL_LENGTH:
            raise CustomerValidationError(
                "email", f"must be at most {MAX_EMAIL_LENGTH} characters"
            )
        if not _EMAIL_PATTERN.match(stripped):
            raise CustomerValidationError("email", "must be a valid email address")
        return stripped
