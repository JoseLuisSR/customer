import uuid
from abc import ABC, abstractmethod

from src.domain.customer import Customer


class CustomerRepository(ABC):
    @abstractmethod
    def create(self, customer: Customer):
        pass

    @abstractmethod
    def get_by_id(self, id: uuid.UUID):
        pass

    @abstractmethod
    def get_all(self) -> list[Customer]:
        pass

    @abstractmethod
    def update_all(sefl, id: uuid.UUID, customer: Customer):
        pass

    @abstractmethod
    def delete_by_id(self, id: uuid.UUID):
        pass
