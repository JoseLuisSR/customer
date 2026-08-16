from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from customers.domain.entities.address import Address
from customers.domain.exceptions import AddressNotFoundError
from customers.domain.repositories.address_repository import AddressRepository
from customers.infrastructure.persistence.mappers.address_mapper import AddressMapper
from customers.infrastructure.persistence.models.address_model import AddressModel


class SQLAlchemyAddressRepository(AddressRepository):
    """Adaptador de salida que implementa el puerto AddressRepository
    usando SQLAlchemy sobre PostgreSQL. Todas las consultas filtran por
    `customer_id` para garantizar el aislamiento entre customers."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, address: Address) -> Address:
        model = AddressMapper.to_new_model(address)
        self._session.add(model)
        self._session.commit()
        return AddressMapper.to_entity(model)

    def get_by_id(
        self, customer_id: int, address_id: int, *, include_deleted: bool = False
    ) -> Address | None:
        model = self._find_model(customer_id, address_id)
        if model is None:
            return None
        if model.deleted_at is not None and not include_deleted:
            return None
        return AddressMapper.to_entity(model)

    def list_active_by_customer(self, customer_id: int) -> list[Address]:
        statement = (
            select(AddressModel)
            .where(
                AddressModel.customer_id == customer_id,
                AddressModel.deleted_at.is_(None),
            )
            .order_by(AddressModel.id)
        )
        models = self._session.scalars(statement).all()
        return [AddressMapper.to_entity(model) for model in models]

    def update(self, address: Address) -> Address:
        model = self._get_model_or_raise(address.customer_id, address.id)
        AddressMapper.apply_to_model(address, model)
        model.updated_at = datetime.now(UTC)
        self._session.commit()
        return AddressMapper.to_entity(model)

    def soft_delete(self, address: Address) -> Address:
        model = self._get_model_or_raise(address.customer_id, address.id)
        model.deleted_at = address.deleted_at
        model.updated_at = datetime.now(UTC)
        self._session.commit()
        return AddressMapper.to_entity(model)

    def _find_model(self, customer_id: int, address_id: int) -> AddressModel | None:
        statement = select(AddressModel).where(
            AddressModel.id == address_id, AddressModel.customer_id == customer_id
        )
        return self._session.scalars(statement).one_or_none()

    def _get_model_or_raise(self, customer_id: int, address_id: int) -> AddressModel:
        model = self._find_model(customer_id, address_id)
        if model is None:
            raise AddressNotFoundError(address_id)
        return model
