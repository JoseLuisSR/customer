"""Adaptador SQLAlchemy del puerto `CustomerRepository`.

Mapea `CustomerModel` (infraestructura) ↔ `Customer` (dominio). Las
lecturas excluyen por defecto los clientes con `status = 'DELETED'`
(`specs/customers/plan.md` §1.1). `get_by_id_for_update` adquiere un
`SELECT ... FOR UPDATE` sobre la fila del cliente (bloqueo pesimista,
`plan.md` §1.4), usado por `CreateAddress` (Fase 2) para proteger RN-003
bajo concurrencia.

`add`/`update` capturan `IntegrityError` de las constraints `UNIQUE`
(`ux_customers_email`, `ux_customers_identification`) y las traducen a
`DuplicateEmailError`/`DuplicateIdentificationError`: es una red de
seguridad ante condiciones de carrera (el flujo normal ya valida
unicidad en la capa de aplicación antes de llegar aquí, ver
`application/customer/support.py::ensure_unique_email_and_identification`).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import NoReturn

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from customers.domain.customer.entities import Customer
from customers.domain.customer.exceptions import (
    DuplicateEmailError,
    DuplicateIdentificationError,
)
from customers.domain.customer.repository import CustomerRepository
from customers.domain.customer.value_objects import Age, CustomerId, Email, Identification, Name
from customers.domain.shared.status import EntityStatus
from customers.infrastructure.persistence.models import CustomerModel

logger = logging.getLogger(__name__)

_UNIQUE_EMAIL_CONSTRAINT = "ux_customers_email"
_UNIQUE_IDENTIFICATION_CONSTRAINT = "ux_customers_identification"


def _model_to_customer(model: CustomerModel) -> Customer:
    return Customer(
        id=CustomerId(model.id),
        name=Name(model.name),
        identification=Identification(model.identification),
        age=Age(model.age),
        email=Email(model.email),
        status=EntityStatus(model.status),
        addresses=[],
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _customer_to_new_model(customer: Customer) -> CustomerModel:
    return CustomerModel(
        id=customer.id.value,
        name=customer.name.value,
        identification=customer.identification.value,
        age=int(customer.age),
        email=customer.email.value,
        status=customer.status.value,
    )


class SqlAlchemyCustomerRepository(CustomerRepository):
    """Adaptador de `CustomerRepository` contra PostgreSQL vía SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, customer: Customer) -> None:
        model = _customer_to_new_model(customer)
        self._session.add(model)
        try:
            self._session.flush()
        except IntegrityError as exc:
            self._session.rollback()
            logger.warning("Violación de constraint única al crear cliente id=%s.", customer.id)
            self._raise_translated(exc, customer)
        # `created_at`/`updated_at` son `server_default=now()` (Fase 3): tras
        # el flush, SQLAlchemy los puebla en `model` vía RETURNING, pero el
        # `customer` de dominio recibido por parámetro sigue con `None`. Se
        # reflejan aquí para que el caller (p. ej. `CreateCustomer.execute`)
        # pueda serializar el mismo objeto con los timestamps reales sin
        # necesitar un `GET` posterior.
        customer.created_at = model.created_at
        customer.updated_at = model.updated_at

    def get_by_id(self, customer_id: CustomerId) -> Customer | None:
        model = self._session.get(CustomerModel, customer_id.value)
        if model is None or model.status == EntityStatus.DELETED.value:
            return None
        return _model_to_customer(model)

    def get_by_id_for_update(self, customer_id: CustomerId) -> Customer | None:
        stmt = (
            select(CustomerModel)
            .where(CustomerModel.id == customer_id.value)
            .where(CustomerModel.status != EntityStatus.DELETED.value)
            .with_for_update()
        )
        model = self._session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        return _model_to_customer(model)

    def list_paginated(self, page: int, page_size: int) -> tuple[list[Customer], int]:
        active_filter = CustomerModel.status != EntityStatus.DELETED.value
        total = self._session.execute(
            select(func.count()).select_from(CustomerModel).where(active_filter)
        ).scalar_one()

        stmt = (
            select(CustomerModel)
            .where(active_filter)
            .order_by(CustomerModel.created_at, CustomerModel.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        models = self._session.execute(stmt).scalars().all()
        return [_model_to_customer(model) for model in models], total

    def find_by_email(
        self, email: Email, *, exclude_customer_id: CustomerId | None = None
    ) -> Customer | None:
        stmt = select(CustomerModel).where(
            CustomerModel.email == email.value,
            CustomerModel.status != EntityStatus.DELETED.value,
        )
        if exclude_customer_id is not None:
            stmt = stmt.where(CustomerModel.id != exclude_customer_id.value)
        model = self._session.execute(stmt).scalar_one_or_none()
        return _model_to_customer(model) if model is not None else None

    def find_by_identification(
        self, identification: Identification, *, exclude_customer_id: CustomerId | None = None
    ) -> Customer | None:
        stmt = select(CustomerModel).where(
            CustomerModel.identification == identification.value,
            CustomerModel.status != EntityStatus.DELETED.value,
        )
        if exclude_customer_id is not None:
            stmt = stmt.where(CustomerModel.id != exclude_customer_id.value)
        model = self._session.execute(stmt).scalar_one_or_none()
        return _model_to_customer(model) if model is not None else None

    def update(self, customer: Customer) -> None:
        model = self._session.get(CustomerModel, customer.id.value)
        if model is None:
            # No debería ocurrir en flujo normal (el caso de uso ya obtuvo el
            # cliente por id antes de llamar a `update`); se registra como
            # advertencia por si la fila fue borrada físicamente por fuera
            # del flujo de la aplicación.
            logger.warning("update() de cliente id=%s no encontró la fila.", customer.id)
            return

        model.name = customer.name.value
        model.identification = customer.identification.value
        model.age = int(customer.age)
        model.email = customer.email.value
        model.status = customer.status.value
        model.updated_at = datetime.now(UTC)
        try:
            self._session.flush()
        except IntegrityError as exc:
            self._session.rollback()
            logger.warning(
                "Violación de constraint única al actualizar cliente id=%s.", customer.id
            )
            self._raise_translated(exc, customer)

    @staticmethod
    def _raise_translated(exc: IntegrityError, customer: Customer) -> NoReturn:
        """Traduce `exc` a la excepción de dominio correspondiente y la lanza.

        Si la constraint violada no es ninguna de las dos `UNIQUE` conocidas
        (`ux_customers_email`/`ux_customers_identification`), se relanza la
        `IntegrityError` original sin envolver, para que quede como error no
        controlado (`ERR-007`) en vez de mapearla incorrectamente a un
        duplicado.
        """
        detail = str(exc.orig) if exc.orig is not None else str(exc)
        if _UNIQUE_EMAIL_CONSTRAINT in detail:
            raise DuplicateEmailError(customer.email.value) from exc
        if _UNIQUE_IDENTIFICATION_CONSTRAINT in detail:
            raise DuplicateIdentificationError(customer.identification.value) from exc
        raise exc
