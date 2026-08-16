"""Modelos SQLAlchemy 2.x (`Mapped`/`mapped_column`) de `customers`/`addresses`.

Reproduce exactamente el modelo de datos de `specs/customers/plan.md`
§1.2/§1.3: tipos de columna, `CHECK` (incluyendo `btrim(...) <> ''` para
los campos de texto obligatorios), `UNIQUE` nombrados (`ux_customers_email`,
`ux_customers_identification`), `FOREIGN KEY ... ON DELETE CASCADE` e
índices (`ix_customers_status`, `ix_addresses_customer_id`,
`ix_addresses_customer_id_status`).

Esta capa (infraestructura) es la única que conoce SQLAlchemy; el dominio
(`domain/customer`, `domain/address`) no importa nada de este módulo. Los
adaptadores de repositorio (`customer_repository.py`, `address_repository.py`)
son los responsables de mapear entre estos modelos y las entidades de
dominio.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    UUID,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Metadata declarativa base de SQLAlchemy para este proyecto."""


class CustomerModel(Base):
    """Modelo ORM de la tabla `customers` (`plan.md` §1.2)."""

    __tablename__ = "customers"
    __table_args__ = (
        CheckConstraint("btrim(name) <> ''", name="ck_customers_name_not_blank"),
        CheckConstraint(
            "btrim(identification) <> ''", name="ck_customers_identification_not_blank"
        ),
        CheckConstraint("age >= 0 AND age <= 120", name="ck_customers_age_range"),
        CheckConstraint("status IN ('ACTIVE', 'DELETED')", name="ck_customers_status"),
        UniqueConstraint("email", name="ux_customers_email"),
        UniqueConstraint("identification", name="ux_customers_identification"),
        Index("ix_customers_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    identification: Mapped[str] = mapped_column(String(64), nullable=False)
    age: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class AddressModel(Base):
    """Modelo ORM de la tabla `addresses` (`plan.md` §1.3)."""

    __tablename__ = "addresses"
    __table_args__ = (
        CheckConstraint("btrim(country) <> ''", name="ck_addresses_country_not_blank"),
        CheckConstraint("btrim(state) <> ''", name="ck_addresses_state_not_blank"),
        CheckConstraint("btrim(city) <> ''", name="ck_addresses_city_not_blank"),
        CheckConstraint("btrim(address) <> ''", name="ck_addresses_address_not_blank"),
        CheckConstraint("btrim(postal_code) <> ''", name="ck_addresses_postal_code_not_blank"),
        CheckConstraint("status IN ('ACTIVE', 'DELETED')", name="ck_addresses_status"),
        Index("ix_addresses_customer_id", "customer_id"),
        Index("ix_addresses_customer_id_status", "customer_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
