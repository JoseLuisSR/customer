import logging
import uuid

from sqlalchemy import Result, delete, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.application.repository.customer_repository import CustomerRepository
from src.domain.customer import Customer
from src.exception.customer_exception import (
    CustomerNotFoundError,
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

        statement = (
            update(CustomerModel)
            .where(CustomerModel.id == id)
            .values(name=customer.name, age=customer.age, email=customer.email)
            .returning(CustomerModel.id)
        )

        try:
            result: Result = db.session.execute(statement)
            db.session.commit()

            if result.scalar_one_or_none() is None:
                raise CustomerNotFoundError(id)

        except SQLAlchemyError as error:
            self._handle_error(error, "update_all")
            raise PersistenceUnavailableError() from error

    def delete_by_id(self, id: uuid.UUID):

        statement = (
            delete(CustomerModel)
            .where(CustomerModel.id == id)
            .returning(CustomerModel.id)
        )

        try:
            result = db.session.execute(statement)
            db.session.commit()

            if result.scalar_one_or_none() is None:
                raise CustomerNotFoundError(id)

        except SQLAlchemyError as error:
            self._handle_error(error, "delete_by_id")
            raise PersistenceUnavailableError() from error

    @staticmethod
    def _to_domain(model: CustomerModel) -> Customer:
        return Customer.restore(
            id=model.id, name=model.name, age=model.age, email=model.email
        )

    def _handle_error(self, error: Exception, operation: str):
        db.session.rollback()
        print(f"The error name is {type(error).__name__} and error is {error}")
        logger.error(
            "SQLAlchemy error",
            extra={
                "operation": operation,
                "sql_alchemy_error": type(error).__name__,
            },
        )
