import pytest
from fakes.in_memory_address_repository import InMemoryAddressRepository
from fakes.in_memory_customer_repository import InMemoryCustomerRepository


@pytest.fixture
def repository() -> InMemoryCustomerRepository:
    return InMemoryCustomerRepository()


@pytest.fixture
def address_repository() -> InMemoryAddressRepository:
    return InMemoryAddressRepository()
