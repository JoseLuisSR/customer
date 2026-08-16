"""Pruebas unitarias de los value objects del agregado `Customer`."""

import uuid

import pytest

from customers.domain.customer.exceptions import (
    InvalidAgeError,
    InvalidEmailError,
    InvalidIdentificationError,
    InvalidNameError,
)
from customers.domain.customer.value_objects import Age, CustomerId, Email, Identification, Name


class TestEmail:
    def test_normalizes_trim_and_lower_case(self) -> None:
        # Arrange
        raw_value = "  John.Doe@Example.com  "

        # Act
        email = Email(raw_value)

        # Assert
        assert email.value == "john.doe@example.com"

    def test_rejects_invalid_format(self) -> None:
        # Arrange
        raw_value = "not-an-email"

        # Act / Assert
        with pytest.raises(InvalidEmailError):
            Email(raw_value)

    def test_validate_returns_none_for_valid_email(self) -> None:
        # Arrange
        raw_value = "valid@example.com"

        # Act
        error = Email.validate(raw_value)

        # Assert
        assert error is None

    def test_validate_returns_field_error_without_raising_for_invalid_email(self) -> None:
        # Arrange
        raw_value = "invalid-email"

        # Act
        error = Email.validate(raw_value)

        # Assert
        assert error is not None
        assert error.code == "VAL-001"
        assert error.field == "email"


class TestName:
    def test_normalizes_trim(self) -> None:
        # Arrange
        raw_value = "  Jane Doe  "

        # Act
        name = Name(raw_value)

        # Assert
        assert name.value == "Jane Doe"

    @pytest.mark.parametrize("raw_value", ["", "   "])
    def test_rejects_blank_after_trim(self, raw_value: str) -> None:
        # Arrange / Act / Assert
        with pytest.raises(InvalidNameError):
            Name(raw_value)

    def test_validate_returns_field_error_for_blank_name(self) -> None:
        # Arrange
        raw_value = "   "

        # Act
        error = Name.validate(raw_value)

        # Assert
        assert error is not None
        assert error.code == "VAL-003"
        assert error.field == "name"


class TestIdentification:
    def test_normalizes_trim_only(self) -> None:
        # Arrange
        raw_value = "  ABC-123  "

        # Act
        identification = Identification(raw_value)

        # Assert
        assert identification.value == "ABC-123"

    def test_does_not_apply_lower_case(self) -> None:
        """Regresión: a diferencia de `Email`, `Identification` no debe
        aplicar `lower()` (decisión de `plan.md` §1.1, Q-001 confirmada)."""
        # Arrange
        raw_value = "AbC-123"

        # Act
        identification = Identification(raw_value)

        # Assert
        assert identification.value == "AbC-123"

    @pytest.mark.parametrize("raw_value", ["", "   "])
    def test_rejects_blank_after_trim(self, raw_value: str) -> None:
        # Arrange / Act / Assert
        with pytest.raises(InvalidIdentificationError):
            Identification(raw_value)

    def test_validate_returns_field_error_for_blank_identification(self) -> None:
        # Arrange
        raw_value = ""

        # Act
        error = Identification.validate(raw_value)

        # Assert
        assert error is not None
        assert error.code == "VAL-004"
        assert error.field == "identification"


class TestAge:
    @pytest.mark.parametrize("raw_value", [0, 1, 120])
    def test_accepts_values_within_range(self, raw_value: int) -> None:
        # Arrange / Act
        age = Age(raw_value)

        # Assert
        assert age.value == raw_value

    def test_rejects_negative_age(self) -> None:
        # Arrange
        raw_value = -1

        # Act / Assert
        with pytest.raises(InvalidAgeError):
            Age(raw_value)

    def test_rejects_age_above_sanity_limit(self) -> None:
        # Arrange
        raw_value = 121

        # Act / Assert
        with pytest.raises(InvalidAgeError):
            Age(raw_value)

    def test_validate_returns_field_error_for_negative_age(self) -> None:
        # Arrange
        raw_value = -5

        # Act
        error = Age.validate(raw_value)

        # Assert
        assert error is not None
        assert error.code == "VAL-005"
        assert error.field == "age"

    def test_validate_returns_none_for_valid_age(self) -> None:
        # Arrange
        raw_value = 30

        # Act
        error = Age.validate(raw_value)

        # Assert
        assert error is None


class TestCustomerId:
    def test_generate_creates_a_uuid_v4(self) -> None:
        # Arrange / Act
        customer_id = CustomerId.generate()

        # Assert
        assert customer_id.value.version == 4

    def test_from_string_parses_a_valid_uuid(self) -> None:
        # Arrange
        raw_value = str(uuid.uuid4())

        # Act
        customer_id = CustomerId.from_string(raw_value)

        # Assert
        assert str(customer_id) == raw_value

    def test_from_string_rejects_invalid_uuid(self) -> None:
        # Arrange
        raw_value = "not-a-uuid"

        # Act / Assert
        with pytest.raises(ValueError):
            CustomerId.from_string(raw_value)
