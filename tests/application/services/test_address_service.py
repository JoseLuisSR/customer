import uuid

import pytest
from pytest_mock import MockerFixture

from src.application.dto.address_dto import AddressPatchRqst, AddressRqst, AddressRsps
from src.application.repository.address_repository import AddressRepository
from src.application.services.address_service import (
    MAX_ADDRESSES_PER_CUSTOMER,
    AddressService,
)
from src.domain.address import Address
from src.exception.address_exception import (
    AddressNotFoundError,
    MaxAddressesPerCustomerError,
)


@pytest.fixture
def repository(mocker: MockerFixture) -> AddressRepository:
    return mocker.create_autospec(AddressRepository, instance=True)


@pytest.fixture
def service(repository: AddressRepository) -> AddressService:
    return AddressService(repository)


def _address_rqst(**overrides: str) -> AddressRqst:
    payload = {
        "country": "Colombia",
        "state": "Bogota D.C.",
        "city": "Bogota",
        "address": "Cra 1 # 2-3",
        "postal_code": "110111",
    }
    payload.update(overrides)
    return AddressRqst(**payload)


def _address(customer_id: uuid.UUID, address_id: uuid.UUID | None = None) -> Address:
    return Address.restore(
        id=address_id or uuid.uuid4(),
        customer_id=customer_id,
        country="Colombia",
        state="Bogota D.C.",
        city="Bogota",
        address="Cra 1 # 2-3",
        postal_code="110111",
    )


class TestCreate:
    def test_raises_when_limit_is_reached_and_does_not_call_create(
        self, service: AddressService, repository: AddressRepository
    ):
        customer_id = uuid.uuid4()
        repository.count_by_customer_id.return_value = MAX_ADDRESSES_PER_CUSTOMER

        with pytest.raises(MaxAddressesPerCustomerError):
            service.create(customer_id, _address_rqst())

        repository.create.assert_not_called()

    def test_happy_path_returns_an_address_rsps(
        self, service: AddressService, repository: AddressRepository
    ):
        customer_id = uuid.uuid4()
        repository.count_by_customer_id.return_value = 0

        result = service.create(customer_id, _address_rqst())

        assert isinstance(result, AddressRsps)
        assert not isinstance(result, Address)
        assert result.country == "Colombia"
        assert result.postal_code == "110111"
        repository.create.assert_called_once()
        created_address = repository.create.call_args.args[0]
        assert isinstance(created_address, Address)
        assert created_address.customer_id == customer_id


class TestGetByIdAndGetAll:
    def test_get_by_id_returns_a_dto_not_the_domain_entity(
        self, service: AddressService, repository: AddressRepository
    ):
        customer_id = uuid.uuid4()
        address_id = uuid.uuid4()
        repository.get_by_id.return_value = _address(customer_id, address_id)

        result = service.get_by_id(customer_id, address_id)

        assert isinstance(result, AddressRsps)
        assert not isinstance(result, Address)

    def test_get_all_returns_a_list_of_dtos(
        self, service: AddressService, repository: AddressRepository
    ):
        customer_id = uuid.uuid4()
        repository.get_all_by_customer_id.return_value = [
            _address(customer_id),
            _address(customer_id),
        ]

        result = service.get_all(customer_id)

        assert len(result) == 2
        assert all(isinstance(item, AddressRsps) for item in result)


class TestUpdatePartial:
    def test_only_overwrites_the_fields_present_in_the_patch(
        self, service: AddressService, repository: AddressRepository
    ):
        customer_id = uuid.uuid4()
        address_id = uuid.uuid4()
        current = _address(customer_id, address_id)
        repository.get_by_id.return_value = current
        repository.update_partial.side_effect = lambda cid, aid, address: address

        patch = AddressPatchRqst(city="Medellin")
        result = service.update_partial(customer_id, address_id, patch)

        passed_address = repository.update_partial.call_args.args[2]
        assert passed_address.city == "Medellin"
        assert passed_address.country == "Colombia"
        assert passed_address.state == "Bogota D.C."
        assert passed_address.address == "Cra 1 # 2-3"
        assert passed_address.postal_code == "110111"
        assert isinstance(result, AddressRsps)
        assert result.city == "Medellin"


class TestReplace:
    def test_raises_when_creating_and_the_limit_is_already_reached(
        self, service: AddressService, repository: AddressRepository
    ):
        customer_id = uuid.uuid4()
        address_id = uuid.uuid4()
        repository.get_by_id.side_effect = AddressNotFoundError(customer_id, address_id)
        repository.count_by_customer_id.return_value = MAX_ADDRESSES_PER_CUSTOMER

        with pytest.raises(MaxAddressesPerCustomerError):
            service.replace(customer_id, address_id, _address_rqst())

        repository.upsert.assert_not_called()

    def test_happy_path_creation_returns_created_true(
        self, service: AddressService, repository: AddressRepository
    ):
        customer_id = uuid.uuid4()
        address_id = uuid.uuid4()
        repository.get_by_id.side_effect = AddressNotFoundError(customer_id, address_id)
        repository.count_by_customer_id.return_value = 0
        repository.upsert.return_value = (_address(customer_id, address_id), True)

        result, created = service.replace(customer_id, address_id, _address_rqst())

        assert created is True
        assert isinstance(result, AddressRsps)

    def test_happy_path_replacement_returns_created_false(
        self, service: AddressService, repository: AddressRepository
    ):
        customer_id = uuid.uuid4()
        address_id = uuid.uuid4()
        existing = _address(customer_id, address_id)
        repository.get_by_id.return_value = existing
        repository.upsert.return_value = (existing, False)

        result, created = service.replace(customer_id, address_id, _address_rqst())

        assert created is False
        assert isinstance(result, AddressRsps)
        repository.count_by_customer_id.assert_not_called()


class TestDeleteById:
    def test_delegates_to_the_repository(
        self, service: AddressService, repository: AddressRepository
    ):
        customer_id = uuid.uuid4()
        address_id = uuid.uuid4()

        service.delete_by_id(customer_id, address_id)

        repository.delete_by_id.assert_called_once_with(customer_id, address_id)
