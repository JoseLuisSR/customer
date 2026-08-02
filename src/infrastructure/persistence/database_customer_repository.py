import uuid

from sqlalchemy import select

from src.application.repository.customer_repository import CustomerRepository
from src.domain.customer import Customer
from src.infrastructure.persistence.customer_model import CustomerModel
from src.infrastructure.persistence.database import db


class DatabaseCustomerRepository(CustomerRepository):
    def create(self, customer: Customer):
        customer_model = CustomerModel(
            id=customer.id, name=customer.name, age=customer.age, email=customer.email
        )
        db.session.add(customer_model)
        db.session.commit()

    def get_by_id(self, id: uuid.UUID):
        customer_model: CustomerModel | None = db.session.get(CustomerModel, id)

        if customer_model is None:
            return None

        return self._to_domain(customer_model)

    def get_all(self) -> list[Customer]:
        statement = select(CustomerModel).order_by(CustomerModel.name)
        customers_model = db.session.execute(statement).scalars().all()
        return [self._to_domain(model) for model in customers_model]

    def delete_by_id(self, id):
        customer_model: CustomerModel | None = db.session.get(CustomerModel, id)

        if customer_model is None:
            return None

        db.session.delete(customer_model)
        db.session.commit()
        return self._to_domain(customer_model)

    @staticmethod
    def _to_domain(model: CustomerModel) -> Customer:
        return Customer.restore(
            id=model.id, name=model.name, age=model.age, email=model.email
        )
