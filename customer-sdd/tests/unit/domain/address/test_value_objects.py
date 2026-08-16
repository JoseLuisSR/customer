"""Pruebas unitarias de los value objects de `Address`."""

import uuid

import pytest

from customers.domain.address.exceptions import InvalidAddressFieldError
from customers.domain.address.value_objects import (
    AddressId,
    City,
    Country,
    PostalCode,
    State,
    StreetAddress,
)

AddressFieldVOType = (
    type[Country] | type[State] | type[City] | type[StreetAddress] | type[PostalCode]
)

_VALUE_OBJECTS_AND_FIELDS: list[tuple[AddressFieldVOType, str]] = [
    (Country, "country"),
    (State, "state"),
    (City, "city"),
    (StreetAddress, "address"),
    (PostalCode, "postal_code"),
]


class TestAddressFieldValueObjects:
    @pytest.mark.parametrize(("value_object_cls", "expected_field"), _VALUE_OBJECTS_AND_FIELDS)
    def test_normalizes_trim(
        self, value_object_cls: AddressFieldVOType, expected_field: str
    ) -> None:
        # Arrange
        raw_value = "  some value  "

        # Act
        instance = value_object_cls(raw_value)

        # Assert
        assert instance.value == "some value"

    @pytest.mark.parametrize(("value_object_cls", "expected_field"), _VALUE_OBJECTS_AND_FIELDS)
    @pytest.mark.parametrize("raw_value", ["", "   "])
    def test_rejects_blank_after_trim(
        self, value_object_cls: AddressFieldVOType, expected_field: str, raw_value: str
    ) -> None:
        # Arrange / Act / Assert
        with pytest.raises(InvalidAddressFieldError):
            value_object_cls(raw_value)

    @pytest.mark.parametrize(("value_object_cls", "expected_field"), _VALUE_OBJECTS_AND_FIELDS)
    def test_validate_returns_field_error_with_expected_code_and_field(
        self, value_object_cls: AddressFieldVOType, expected_field: str
    ) -> None:
        # Arrange
        raw_value = "   "

        # Act
        error = value_object_cls.validate(raw_value)

        # Assert
        assert error is not None
        assert error.code == "VAL-009"
        assert error.field == expected_field

    @pytest.mark.parametrize(("value_object_cls", "expected_field"), _VALUE_OBJECTS_AND_FIELDS)
    def test_validate_returns_none_for_valid_value(
        self, value_object_cls: AddressFieldVOType, expected_field: str
    ) -> None:
        # Arrange
        raw_value = "valid value"

        # Act
        error = value_object_cls.validate(raw_value)

        # Assert
        assert error is None

    def test_postal_code_is_required_without_country_exception(self) -> None:
        """VAL-009/Q-005: `postal_code` es obligatorio para todos los países,
        sin excepción."""
        # Arrange
        raw_value = ""

        # Act
        error = PostalCode.validate(raw_value)

        # Assert
        assert error is not None
        assert error.field == "postal_code"


class TestAddressId:
    def test_generate_creates_a_uuid_v4(self) -> None:
        # Arrange / Act
        address_id = AddressId.generate()

        # Assert
        assert address_id.value.version == 4

    def test_from_string_parses_a_valid_uuid(self) -> None:
        # Arrange
        raw_value = str(uuid.uuid4())

        # Act
        address_id = AddressId.from_string(raw_value)

        # Assert
        assert str(address_id) == raw_value

    def test_from_string_rejects_invalid_uuid(self) -> None:
        # Arrange
        raw_value = "not-a-uuid"

        # Act / Assert
        with pytest.raises(ValueError):
            AddressId.from_string(raw_value)
