from __future__ import annotations

from customers.domain.entities.customer import Customer
from customers.infrastructure.persistence.models.customer_model import CustomerModel


class CustomerMapper:
    """Convierte entre la entidad de dominio Customer y el modelo ORM
    CustomerModel, para que el dominio nunca dependa de SQLAlchemy."""

    @staticmethod
    def to_entity(model: CustomerModel) -> Customer:
        return Customer(
            id=model.id,
            name=model.name,
            age=model.age,
            email=model.email,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )

    @staticmethod
    def to_new_model(customer: Customer) -> CustomerModel:
        return CustomerModel(name=customer.name, age=customer.age, email=customer.email)

    @staticmethod
    def apply_to_model(customer: Customer, model: CustomerModel) -> None:
        model.name = customer.name
        model.age = customer.age
        model.email = customer.email
        model.deleted_at = customer.deleted_at
