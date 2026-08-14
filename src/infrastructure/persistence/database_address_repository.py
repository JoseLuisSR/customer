import logging
import uuid

from sqlalchemy import Result, delete, func, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.application.repository.address_repository import AddressRepository
from src.domain.address import Address
from src.exception.address_exception import AddressNotFoundError
from src.exception.customer_exception import (
    CustomerNotFoundError,
    PersistenceUnavailableError,
)
from src.infrastructure.persistence.address_model import AddressModel
from src.infrastructure.persistence.database import db

logger = logging.getLogger(__name__)


class DatabaseAddressRepository(AddressRepository):
    def create(self, address: Address) -> None:
        address_model = self._to_model(address)

        try:
            db.session.add(address_model)
            db.session.commit()
        except IntegrityError as error:
            self._handle_error(error, "create")
            raise CustomerNotFoundError(address.customer_id) from error
        except SQLAlchemyError as error:
            self._handle_error(error, "create")
            raise PersistenceUnavailableError() from error

    def get_by_id(self, customer_id: uuid.UUID, address_id: uuid.UUID) -> Address:
        statement = select(AddressModel).where(
            AddressModel.id == address_id, AddressModel.customer_id == customer_id
        )

        try:
            address_model: AddressModel | None = db.session.execute(
                statement
            ).scalar_one_or_none()
        except SQLAlchemyError as error:
            self._handle_error(error, "get_by_id")
            raise PersistenceUnavailableError() from error

        if address_model is None:
            raise AddressNotFoundError(customer_id, address_id)

        return self._to_domain(address_model)

    def get_all_by_customer_id(self, customer_id: uuid.UUID) -> list[Address]:
        statement = (
            select(AddressModel)
            .where(AddressModel.customer_id == customer_id)
            .order_by(AddressModel.country, AddressModel.city)
        )

        try:
            addresses_model = db.session.execute(statement).scalars().all()
            return [self._to_domain(model) for model in addresses_model]
        except SQLAlchemyError as error:
            self._handle_error(error, "get_all_by_customer_id")
            raise PersistenceUnavailableError() from error

    def count_by_customer_id(self, customer_id: uuid.UUID) -> int:
        statement = (
            select(func.count())
            .select_from(AddressModel)
            .where(AddressModel.customer_id == customer_id)
        )

        try:
            count: int = db.session.execute(statement).scalar_one()
            return count
        except SQLAlchemyError as error:
            self._handle_error(error, "count_by_customer_id")
            raise PersistenceUnavailableError() from error

    def update_partial(
        self, customer_id: uuid.UUID, address_id: uuid.UUID, address: Address
    ) -> Address:
        statement = (
            update(AddressModel)
            .where(
                AddressModel.id == address_id, AddressModel.customer_id == customer_id
            )
            .values(
                country=address.country,
                state=address.state,
                city=address.city,
                address=address.address,
                postal_code=address.postal_code,
            )
            .returning(AddressModel.id)
        )

        try:
            result: Result = db.session.execute(statement)
            db.session.commit()

            if result.scalar_one_or_none() is None:
                raise AddressNotFoundError(customer_id, address_id)

        except SQLAlchemyError as error:
            self._handle_error(error, "update_partial")
            raise PersistenceUnavailableError() from error

        return address

    def upsert(
        self, customer_id: uuid.UUID, address_id: uuid.UUID, address: Address
    ) -> tuple[Address, bool]:
        select_statement = select(AddressModel).where(
            AddressModel.id == address_id, AddressModel.customer_id == customer_id
        )

        try:
            existing_model: AddressModel | None = db.session.execute(
                select_statement
            ).scalar_one_or_none()

            if existing_model is None:
                address_model = self._to_model(address)
                db.session.add(address_model)
                db.session.commit()
                return self._to_domain(address_model), True

            update_statement = (
                update(AddressModel)
                .where(
                    AddressModel.id == address_id,
                    AddressModel.customer_id == customer_id,
                )
                .values(
                    country=address.country,
                    state=address.state,
                    city=address.city,
                    address=address.address,
                    postal_code=address.postal_code,
                )
            )
            db.session.execute(update_statement)
            db.session.commit()
            return address, False

        except IntegrityError as error:
            self._handle_error(error, "upsert")
            raise CustomerNotFoundError(customer_id) from error
        except SQLAlchemyError as error:
            self._handle_error(error, "upsert")
            raise PersistenceUnavailableError() from error

    def delete_by_id(self, customer_id: uuid.UUID, address_id: uuid.UUID) -> None:
        statement = (
            delete(AddressModel)
            .where(
                AddressModel.id == address_id, AddressModel.customer_id == customer_id
            )
            .returning(AddressModel.id)
        )

        try:
            result = db.session.execute(statement)
            db.session.commit()

            if result.scalar_one_or_none() is None:
                raise AddressNotFoundError(customer_id, address_id)

        except SQLAlchemyError as error:
            self._handle_error(error, "delete_by_id")
            raise PersistenceUnavailableError() from error

    @staticmethod
    def _to_domain(model: AddressModel) -> Address:
        return Address.restore(
            id=model.id,
            customer_id=model.customer_id,
            country=model.country,
            state=model.state,
            city=model.city,
            address=model.address,
            postal_code=model.postal_code,
        )

    @staticmethod
    def _to_model(address: Address) -> AddressModel:
        return AddressModel(
            id=address.id,
            customer_id=address.customer_id,
            country=address.country,
            state=address.state,
            city=address.city,
            address=address.address,
            postal_code=address.postal_code,
        )

    def _handle_error(self, error: Exception, operation: str) -> None:
        db.session.rollback()
        logger.error(
            "SQLAlchemy error",
            extra={
                "operation": operation,
                "sql_alchemy_error": type(error).__name__,
            },
        )
