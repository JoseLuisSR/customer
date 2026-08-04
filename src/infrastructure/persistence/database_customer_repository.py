import logging
import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.application.repository.customer_repository import CustomerRepository
from src.domain.customer import Customer
from src.exception.customer_exception import (
    CustomerWithIDAlreadyExistsError,
    PersistenceUnavailableError,
)
from src.infrastructure.persistence.customer_model import CustomerModel
from src.infrastructure.persistence.database import db

logger = logging.getLogger(__name__)


class DatabaseCustomerRepository(CustomerRepository):
    def create(self, customer: Customer):
        customer_model = CustomerModel(
            id=customer.id, name=customer.name, age=customer.age, email=customer.email
        )

        try:
            db.session.add(customer_model)
            db.session.commit()
        except IntegrityError as error:
            self._handle_error(error, "create")
            raise CustomerWithIDAlreadyExistsError(customer_model.id) from error
        except SQLAlchemyError as error:
            self._handle_error(error, "create")
            raise PersistenceUnavailableError() from error

    def get_by_id(self, id: uuid.UUID):

        try:
            customer_model: CustomerModel | None = db.session.get(CustomerModel, id)
        except SQLAlchemyError as error:
            self._handle_error(error, "get_by_id")
            raise PersistenceUnavailableError() from error

        if customer_model is None:
            return None

        return self._to_domain(customer_model)

    def get_all(self) -> list[Customer]:
        statement = select(CustomerModel).order_by(CustomerModel.name)
        try:
            customers_model = db.session.execute(statement).scalars().all()
            return [self._to_domain(model) for model in customers_model]
        except SQLAlchemyError as error:
            self._handle_error(error, "get_all")
            raise SQLAlchemyError(error)

    def update_all(self, id: uuid.UUID, customer: Customer):
        customer_model: CustomerModel | None = db.session.get(CustomerModel, id)

        if customer_model is None:
            return None

        customer_model.name = customer.name
        customer_model.age = customer.age
        customer_model.email = customer.email
        db.session.commit()
        return self._to_domain(customer_model)

    def delete_by_id(self, id: uuid.UUID):
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

    def _handle_error(self, error: Exception, operation: str):
        db.session.rollback()
        logger.error(
            "SQLAlchemy error",
            extra={
                "operation": operation,
                "sql_alchemy_error": type(error).__name__,
            },
        )
