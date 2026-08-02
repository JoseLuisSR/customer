import uuid

from src.application.dto.customer_dto import CustomerRqst, CustomerRsps
from src.application.repository.customer_repository import CustomerRepository
from src.domain.customer import Customer
from src.exception.customer_exception import CustomerNotFoundException


class CustomerService:
    def __init__(self, repository: CustomerRepository):
        self.repository = repository

    def create(self, customer_rqst: CustomerRqst) -> CustomerRsps:
        customer: Customer = Customer.create(
            customer_rqst.name, customer_rqst.age, customer_rqst.email
        )
        self.repository.create(customer)
        return CustomerRsps(
            id=customer.id, name=customer.name, age=customer.age, email=customer.email
        )

    def get_by_id(self, id: uuid.UUID):
        customer: Customer = self.repository.get_by_id(id)

        if customer is None:
            raise CustomerNotFoundException(id)

        return CustomerRsps(
            id=customer.id, name=customer.name, age=customer.age, email=customer.email
        )

    def get_all(self) -> list[CustomerRsps]:
        customers = self.repository.get_all()
        return [
            CustomerRsps(
                id=customer.id,
                name=customer.name,
                age=customer.age,
                email=customer.email,
            )
            for customer in customers
        ]

    def delete_by_id(self, id: uuid.UUID):
        customer: Customer = self.repository.delete_by_id(id)

        if customer is None:
            raise CustomerNotFoundException(id)

        return CustomerRsps(
            id=customer.id, name=customer.name, age=customer.age, email=customer.email
        )
