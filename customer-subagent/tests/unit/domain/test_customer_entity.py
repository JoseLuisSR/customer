from datetime import UTC, datetime

import pytest

from customers.domain.entities.customer import (
    MAX_AGE,
    MAX_EMAIL_LENGTH,
    MAX_NAME_LENGTH,
    MIN_AGE,
    Customer,
)
from customers.domain.exceptions import (
    CustomerAlreadyDeletedError,
    CustomerValidationError,
)


def make_customer(**overrides):
    fields = {"name": "Ada Lovelace", "age": 30, "email": "ada@example.com"}
    fields.update(overrides)
    return Customer(**fields)


class TestConstruction:
    def test_creates_customer_with_valid_data(self):
        customer = make_customer()

        assert customer.name == "Ada Lovelace"
        assert customer.age == 30
        assert customer.email == "ada@example.com"
        assert customer.id is None
        assert customer.is_deleted() is False

    def test_strips_surrounding_whitespace_from_name_and_email(self):
        customer = make_customer(name="  Ada  ", email="  ada@example.com  ")

        assert customer.name == "Ada"
        assert customer.email == "ada@example.com"

    def test_accepts_boundary_ages(self):
        assert make_customer(age=MIN_AGE).age == MIN_AGE
        assert make_customer(age=MAX_AGE).age == MAX_AGE


class TestNameValidation:
    def test_rejects_empty_name(self):
        with pytest.raises(CustomerValidationError) as exc_info:
            make_customer(name="")

        assert exc_info.value.field == "name"

    def test_rejects_whitespace_only_name(self):
        with pytest.raises(CustomerValidationError):
            make_customer(name="   ")

    def test_rejects_name_longer_than_max_length(self):
        with pytest.raises(CustomerValidationError):
            make_customer(name="a" * (MAX_NAME_LENGTH + 1))

    def test_rejects_non_string_name(self):
        with pytest.raises(CustomerValidationError):
            make_customer(name=123)


class TestAgeValidation:
    def test_rejects_age_below_minimum(self):
        with pytest.raises(CustomerValidationError) as exc_info:
            make_customer(age=MIN_AGE - 1)

        assert exc_info.value.field == "age"

    def test_rejects_age_above_maximum(self):
        with pytest.raises(CustomerValidationError):
            make_customer(age=MAX_AGE + 1)

    def test_rejects_non_integer_age(self):
        with pytest.raises(CustomerValidationError):
            make_customer(age="30")

    def test_rejects_boolean_age(self):
        with pytest.raises(CustomerValidationError):
            make_customer(age=True)


class TestEmailValidation:
    def test_rejects_empty_email(self):
        with pytest.raises(CustomerValidationError) as exc_info:
            make_customer(email="")

        assert exc_info.value.field == "email"

    def test_rejects_email_without_at_sign(self):
        with pytest.raises(CustomerValidationError):
            make_customer(email="ada.example.com")

    def test_rejects_email_without_domain(self):
        with pytest.raises(CustomerValidationError):
            make_customer(email="ada@example")

    def test_rejects_email_longer_than_max_length(self):
        local_part = "a" * (MAX_EMAIL_LENGTH - len("@example.com") + 1)
        with pytest.raises(CustomerValidationError):
            make_customer(email=f"{local_part}@example.com")

    def test_rejects_non_string_email(self):
        with pytest.raises(CustomerValidationError):
            make_customer(email=123)


class TestMutators:
    def test_rename_validates_new_value(self):
        customer = make_customer()

        customer.rename("Grace Hopper")

        assert customer.name == "Grace Hopper"
        with pytest.raises(CustomerValidationError):
            customer.rename("")

    def test_update_age_validates_new_value(self):
        customer = make_customer()

        customer.update_age(45)

        assert customer.age == 45
        with pytest.raises(CustomerValidationError):
            customer.update_age(-1)

    def test_update_email_validates_new_value(self):
        customer = make_customer()

        customer.update_email("grace@example.com")

        assert customer.email == "grace@example.com"
        with pytest.raises(CustomerValidationError):
            customer.update_email("invalid")


class TestSoftDelete:
    def test_mark_deleted_sets_deleted_at(self):
        customer = make_customer()
        deleted_at = datetime.now(UTC)

        customer.mark_deleted(deleted_at)

        assert customer.is_deleted() is True
        assert customer.deleted_at == deleted_at

    def test_mark_deleted_twice_raises(self):
        customer = make_customer()
        customer.mark_deleted(datetime.now(UTC))

        with pytest.raises(CustomerAlreadyDeletedError):
            customer.mark_deleted(datetime.now(UTC))
