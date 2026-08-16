import uuid

import pytest
from pydantic import ValidationError

from src.application.dto.address_dto import AddressPatchRqst, AddressRqst, AddressRsps

VALID_FIELDS = {
    "country": "Colombia",
    "state": "Bogota D.C.",
    "city": "Bogota",
    "address": "Cra 1 # 2-3",
}


class TestAddressRqstAlias:
    def test_accepts_the_postal_code_alias(self):
        rqst = AddressRqst.model_validate({**VALID_FIELDS, "postal-code": "110111"})

        assert rqst.postal_code == "110111"

    def test_accepts_the_postal_code_field_name(self):
        rqst = AddressRqst(**VALID_FIELDS, postal_code="110111")

        assert rqst.postal_code == "110111"


class TestAddressRqstValidation:
    @pytest.mark.parametrize(
        "field, value",
        [
            ("country", "C"),  # below min_length=2
            ("country", "C" * 101),  # above max_length=100
            ("state", "S"),
            ("state", "S" * 101),
            ("city", "C"),
            ("city", "C" * 101),
            ("address", "Ad"),  # below min_length=3
            ("address", "A" * 201),  # above max_length=200
            ("postal_code", "1"),  # below min_length=3
            ("postal_code", "1" * 16),  # above max_length=15
        ],
    )
    def test_rejects_out_of_range_lengths(self, field: str, value: str):
        payload = {**VALID_FIELDS, "postal-code": "110111"}
        payload["postal-code" if field == "postal_code" else field] = value

        with pytest.raises(ValidationError):
            AddressRqst.model_validate(payload)


class TestAddressPatchRqst:
    def test_empty_patch_is_valid_with_all_fields_none(self):
        patch = AddressPatchRqst()

        assert patch.country is None
        assert patch.state is None
        assert patch.city is None
        assert patch.address is None
        assert patch.postal_code is None


class TestAddressRsps:
    def test_model_dump_by_alias_uses_the_postal_code_hyphen_key(self):
        rsps = AddressRsps(
            id=uuid.uuid4(),
            country="Colombia",
            state="Bogota D.C.",
            city="Bogota",
            address="Cra 1 # 2-3",
            postal_code="110111",
        )

        dumped = rsps.model_dump(by_alias=True)

        assert dumped["postal-code"] == "110111"
        assert "postal_code" not in dumped
