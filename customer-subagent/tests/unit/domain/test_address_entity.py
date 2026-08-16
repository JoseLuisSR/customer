from datetime import UTC, datetime

import pytest

from customers.domain.entities.address import (
    MAX_ADDRESS_LINE_LENGTH,
    MAX_CITY_LENGTH,
    MAX_COUNTRY_LENGTH,
    MAX_POSTAL_CODE_LENGTH,
    MAX_STATE_LENGTH,
    Address,
)
from customers.domain.exceptions import (
    AddressAlreadyDeletedError,
    AddressValidationError,
)


def make_address(**overrides):
    fields = {
        "customer_id": 1,
        "country": "Colombia",
        "state": "Meta",
        "city": "Villavicencio",
        "postal_code": "50001",
        "address_line": "Calle 10 #5-20",
    }
    fields.update(overrides)
    return Address(**fields)


class TestConstruction:
    def test_creates_address_with_valid_data(self):
        address = make_address()

        assert address.customer_id == 1
        assert address.country == "Colombia"
        assert address.state == "Meta"
        assert address.city == "Villavicencio"
        assert address.postal_code == "50001"
        assert address.address_line == "Calle 10 #5-20"
        assert address.id is None
        assert address.is_deleted() is False

    def test_strips_surrounding_whitespace(self):
        address = make_address(country="  Colombia  ", city="  Villavicencio  ")

        assert address.country == "Colombia"
        assert address.city == "Villavicencio"


class TestCustomerIdValidation:
    def test_rejects_non_integer_customer_id(self):
        with pytest.raises(AddressValidationError) as exc_info:
            make_address(customer_id="1")

        assert exc_info.value.field == "customer_id"

    def test_rejects_boolean_customer_id(self):
        with pytest.raises(AddressValidationError):
            make_address(customer_id=True)

    def test_rejects_zero_customer_id(self):
        with pytest.raises(AddressValidationError):
            make_address(customer_id=0)

    def test_rejects_negative_customer_id(self):
        with pytest.raises(AddressValidationError):
            make_address(customer_id=-1)


FIELD_CASES = [
    ("country", MAX_COUNTRY_LENGTH),
    ("state", MAX_STATE_LENGTH),
    ("city", MAX_CITY_LENGTH),
    ("postal_code", MAX_POSTAL_CODE_LENGTH),
    ("address_line", MAX_ADDRESS_LINE_LENGTH),
]


@pytest.mark.parametrize(("field", "max_length"), FIELD_CASES)
class TestTextFieldValidation:
    def test_rejects_empty(self, field, max_length):
        with pytest.raises(AddressValidationError) as exc_info:
            make_address(**{field: ""})

        assert exc_info.value.field == field

    def test_rejects_whitespace_only(self, field, max_length):
        with pytest.raises(AddressValidationError):
            make_address(**{field: "   "})

    def test_rejects_value_longer_than_max_length(self, field, max_length):
        with pytest.raises(AddressValidationError):
            make_address(**{field: "a" * (max_length + 1)})

    def test_rejects_non_string(self, field, max_length):
        with pytest.raises(AddressValidationError):
            make_address(**{field: 123})

    def test_accepts_value_at_max_length(self, field, max_length):
        address = make_address(**{field: "a" * max_length})

        assert getattr(address, field) == "a" * max_length


class TestMutators:
    def test_update_country_validates_new_value(self):
        address = make_address()

        address.update_country("Argentina")

        assert address.country == "Argentina"
        with pytest.raises(AddressValidationError):
            address.update_country("")

    def test_update_state_validates_new_value(self):
        address = make_address()

        address.update_state("Cordoba")

        assert address.state == "Cordoba"
        with pytest.raises(AddressValidationError):
            address.update_state("")

    def test_update_city_validates_new_value(self):
        address = make_address()

        address.update_city("Bogota")

        assert address.city == "Bogota"
        with pytest.raises(AddressValidationError):
            address.update_city("")

    def test_update_postal_code_validates_new_value(self):
        address = make_address()

        address.update_postal_code("110111")

        assert address.postal_code == "110111"
        with pytest.raises(AddressValidationError):
            address.update_postal_code("")

    def test_update_address_line_validates_new_value(self):
        address = make_address()

        address.update_address_line("Carrera 7 #10-20")

        assert address.address_line == "Carrera 7 #10-20"
        with pytest.raises(AddressValidationError):
            address.update_address_line("")


class TestSoftDelete:
    def test_mark_deleted_sets_deleted_at(self):
        address = make_address()
        deleted_at = datetime.now(UTC)

        address.mark_deleted(deleted_at)

        assert address.is_deleted() is True
        assert address.deleted_at == deleted_at

    def test_mark_deleted_twice_raises(self):
        address = make_address()
        address.mark_deleted(datetime.now(UTC))

        with pytest.raises(AddressAlreadyDeletedError):
            address.mark_deleted(datetime.now(UTC))
