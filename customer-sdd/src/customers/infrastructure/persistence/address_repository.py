"""Adaptador SQLAlchemy del puerto `AddressRepository`.

Mapea `AddressModel` (infraestructura) ↔ `Address` (dominio). Las lecturas
filtran por defecto `status <> 'DELETED'` (`specs/customers/plan.md` §1.1),
salvo cuando el caller solicita explícitamente `include_deleted=True`
(usado por `DeleteCustomer`, Fase 2, para mostrar el estado final de las
direcciones ya eliminadas en la respuesta).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from customers.domain.address.entities import Address
from customers.domain.address.repository import AddressRepository
from customers.domain.address.value_objects import (
    AddressId,
    City,
    Country,
    PostalCode,
    State,
    StreetAddress,
)
from customers.domain.customer.value_objects import CustomerId
from customers.domain.shared.status import EntityStatus
from customers.infrastructure.persistence.models import AddressModel

logger = logging.getLogger(__name__)


def _model_to_address(model: AddressModel) -> Address:
    return Address(
        id=AddressId(model.id),
        customer_id=CustomerId(model.customer_id),
        country=Country(model.country),
        state=State(model.state),
        city=City(model.city),
        street_address=StreetAddress(model.address),
        postal_code=PostalCode(model.postal_code),
        status=EntityStatus(model.status),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _address_to_new_model(address: Address) -> AddressModel:
    return AddressModel(
        id=address.id.value,
        customer_id=address.customer_id.value,
        country=address.country.value,
        state=address.state.value,
        city=address.city.value,
        address=address.street_address.value,
        postal_code=address.postal_code.value,
        status=address.status.value,
    )


class SqlAlchemyAddressRepository(AddressRepository):
    """Adaptador de `AddressRepository` contra PostgreSQL vía SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, address: Address) -> None:
        model = _address_to_new_model(address)
        self._session.add(model)
        # `flush()` (no `commit()`): el límite transaccional queda a cargo
        # del caller (unidad de trabajo por request en Fase 4, o del test de
        # integración), para que `CreateCustomer` pueda persistir cliente y
        # direcciones de forma atómica en una sola transacción.
        self._session.flush()
        # Mismo caso que `SqlAlchemyCustomerRepository.add`: `created_at`/
        # `updated_at` son `server_default=now()` y solo quedan poblados en
        # `model` tras el flush; se reflejan en `address` para que el caller
        # (p. ej. `CreateAddress.execute`) los tenga disponibles de inmediato.
        address.created_at = model.created_at
        address.updated_at = model.updated_at

    def get_by_id(self, address_id: AddressId) -> Address | None:
        model = self._session.get(AddressModel, address_id.value)
        if model is None or model.status == EntityStatus.DELETED.value:
            return None
        return _model_to_address(model)

    def list_by_customer(
        self, customer_id: CustomerId, *, include_deleted: bool = False
    ) -> list[Address]:
        stmt = select(AddressModel).where(AddressModel.customer_id == customer_id.value)
        if not include_deleted:
            stmt = stmt.where(AddressModel.status != EntityStatus.DELETED.value)
        stmt = stmt.order_by(AddressModel.created_at, AddressModel.id)
        models = self._session.execute(stmt).scalars().all()
        return [_model_to_address(model) for model in models]

    def count_active_by_customer(self, customer_id: CustomerId) -> int:
        stmt = (
            select(func.count())
            .select_from(AddressModel)
            .where(
                AddressModel.customer_id == customer_id.value,
                AddressModel.status != EntityStatus.DELETED.value,
            )
        )
        return self._session.execute(stmt).scalar_one()

    def update(self, address: Address) -> None:
        model = self._session.get(AddressModel, address.id.value)
        if model is None:
            # No debería ocurrir en flujo normal (el caso de uso ya obtuvo la
            # dirección por id antes de llamar a `update`).
            logger.warning("update() de dirección id=%s no encontró la fila.", address.id)
            return

        model.country = address.country.value
        model.state = address.state.value
        model.city = address.city.value
        model.address = address.street_address.value
        model.postal_code = address.postal_code.value
        model.status = address.status.value
        model.updated_at = datetime.now(UTC)
        self._session.flush()

    def mark_all_deleted_by_customer(self, customer_id: CustomerId) -> None:
        stmt = select(AddressModel).where(
            AddressModel.customer_id == customer_id.value,
            AddressModel.status != EntityStatus.DELETED.value,
        )
        models = self._session.execute(stmt).scalars().all()
        now = datetime.now(UTC)
        for model in models:
            model.status = EntityStatus.DELETED.value
            model.updated_at = now
        self._session.flush()
