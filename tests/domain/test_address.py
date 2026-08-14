import uuid

import pytest

from src.domain.address import Address


def _build_address() -> Address:
    return Address.create(
        customer_id=uuid.uuid4(),
        country="Colombia",
        state="Bogota D.C.",
        city="Bogota",
        address="Cra 1 # 2-3",
        postal_code="110111",
    )


class TestAddressCreate:
    def test_generates_a_uuid_id(self):
        address = _build_address()

        assert isinstance(address.id, uuid.UUID)

    def test_generates_a_different_uuid_on_each_call(self):
        first = _build_address()
        second = _build_address()

        assert first.id != second.id


class TestAddressRestore:
    def test_reconstructs_exactly_the_given_values(self):
        address_id = uuid.uuid4()
        customer_id = uuid.uuid4()

        address = Address.restore(
            id=address_id,
            customer_id=customer_id,
            country="Colombia",
            state="Bogota D.C.",
            city="Bogota",
            address="Cra 1 # 2-3",
            postal_code="110111",
        )

        assert address.id == address_id
        assert address.customer_id == customer_id
        assert address.country == "Colombia"
        assert address.state == "Bogota D.C."
        assert address.city == "Bogota"
        assert address.address == "Cra 1 # 2-3"
        assert address.postal_code == "110111"

    def test_does_not_generate_a_new_id(self):
        address_id = uuid.uuid4()

        address = Address.restore(
            id=address_id,
            customer_id=uuid.uuid4(),
            country="Colombia",
            state="Bogota D.C.",
            city="Bogota",
            address="Cra 1 # 2-3",
            postal_code="110111",
        )

        assert address.id is address_id


class TestAddressSetters:
    @pytest.mark.parametrize(
        "attribute, value",
        [
            ("country", "Mexico"),
            ("state", "Jalisco"),
            ("city", "Guadalajara"),
            ("address", "Av. Siempre Viva 742"),
            ("postal_code", "45000"),
        ],
    )
    def test_setter_mutates_only_the_target_attribute(self, attribute: str, value: str):
        address = _build_address()
        original = {
            "id": address.id,
            "customer_id": address.customer_id,
            "country": address.country,
            "state": address.state,
            "city": address.city,
            "address": address.address,
            "postal_code": address.postal_code,
        }

        setattr(address, attribute, value)

        assert getattr(address, attribute) == value
        for other_attribute, other_value in original.items():
            if other_attribute == attribute:
                continue
            assert getattr(address, other_attribute) == other_value


class TestAddressReadOnlyAttributes:
    def test_id_has_no_setter(self):
        address = _build_address()

        with pytest.raises(AttributeError):
            address.id = uuid.uuid4()

    def test_customer_id_has_no_setter(self):
        address = _build_address()

        with pytest.raises(AttributeError):
            address.customer_id = uuid.uuid4()
