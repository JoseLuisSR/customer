from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from customers.domain.entities.customer import Customer
from customers.domain.exceptions import (
    CustomerEmailAlreadyExistsError,
    CustomerNotFoundError,
)
from customers.domain.repositories.customer_repository import CustomerRepository
from customers.infrastructure.persistence.mappers.customer_mapper import CustomerMapper
from customers.infrastructure.persistence.models.customer_model import CustomerModel


class SQLAlchemyCustomerRepository(CustomerRepository):
    """Adaptador de salida que implementa el puerto CustomerRepository
    usando SQLAlchemy sobre PostgreSQL."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, customer: Customer) -> Customer:
        model = CustomerMapper.to_new_model(customer)
        self._session.add(model)
        self._commit_or_raise_email_conflict(customer.email)
        return CustomerMapper.to_entity(model)

    def get_by_id(
        self, customer_id: int, *, include_deleted: bool = False
    ) -> Customer | None:
        model = self._session.get(CustomerModel, customer_id)
        if model is None:
            return None
        if model.deleted_at is not None and not include_deleted:
            return None
        return CustomerMapper.to_entity(model)

    def list_active(self) -> list[Customer]:
        statement = (
            select(CustomerModel)
            .where(CustomerModel.deleted_at.is_(None))
            .order_by(CustomerModel.id)
        )
        models = self._session.scalars(statement).all()
        return [CustomerMapper.to_entity(model) for model in models]

    def update(self, customer: Customer) -> Customer:
        model = self._get_model_or_raise(customer.id)
        CustomerMapper.apply_to_model(customer, model)
        model.updated_at = datetime.now(UTC)
        self._commit_or_raise_email_conflict(customer.email)
        return CustomerMapper.to_entity(model)

    def soft_delete(self, customer: Customer) -> Customer:
        model = self._get_model_or_raise(customer.id)
        model.deleted_at = customer.deleted_at
        model.updated_at = datetime.now(UTC)
        self._session.commit()
        return CustomerMapper.to_entity(model)

    def _get_model_or_raise(self, customer_id: int) -> CustomerModel:
        model = self._session.get(CustomerModel, customer_id)
        if model is None:
            raise CustomerNotFoundError(customer_id)
        return model

    def _commit_or_raise_email_conflict(self, email: str) -> None:
        try:
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            if "email" in str(exc.orig).lower():
                raise CustomerEmailAlreadyExistsError(email) from exc
            raise
