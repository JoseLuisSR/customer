import uuid
from abc import ABC, abstractmethod

from src.domain.address import Address


class AddressRepository(ABC):
    @abstractmethod
    def create(self, address: Address) -> None:
        pass

    @abstractmethod
    def get_by_id(self, customer_id: uuid.UUID, address_id: uuid.UUID) -> Address:
        pass

    @abstractmethod
    def get_all_by_customer_id(self, customer_id: uuid.UUID) -> list[Address]:
        pass

    @abstractmethod
    def count_by_customer_id(self, customer_id: uuid.UUID) -> int:
        pass

    @abstractmethod
    def update_partial(
        self, customer_id: uuid.UUID, address_id: uuid.UUID, address: Address
    ) -> Address:
        pass

    @abstractmethod
    def upsert(
        self, customer_id: uuid.UUID, address_id: uuid.UUID, address: Address
    ) -> tuple[Address, bool]:
        pass

    @abstractmethod
    def delete_by_id(self, customer_id: uuid.UUID, address_id: uuid.UUID) -> None:
        pass
