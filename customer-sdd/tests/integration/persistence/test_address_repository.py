"""Pruebas de integración de `SqlAlchemyAddressRepository` contra Postgres real.

Referencias: `specs/customers/implementation-plan.md` §8.1, `specs/customers/
plan.md` §6.2/§1.3. Cubre:

- La `FOREIGN KEY addresses.customer_id -> customers.id`: insertar una
  dirección para un cliente inexistente viola la constraint (verificado a
  nivel de base de datos real, no solo la validación de aplicación que ya
  ocurre antes en `CreateAddress`).
- Filtrado por `status <> 'DELETED'` en `get_by_id`/`list_by_customer`.
- `count_active_by_customer` sobre el conteo de direcciones `ACTIVE`.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from customers.domain.address.entities import Address
from customers.domain.address.value_objects import (
    City,
    Country,
    PostalCode,
    State,
    StreetAddress,
)
from customers.domain.customer.entities import Customer
from customers.domain.customer.value_objects import Age, CustomerId, Email, Identification, Name
from customers.domain.shared.status import EntityStatus
from customers.infrastructure.persistence.address_repository import SqlAlchemyAddressRepository
from customers.infrastructure.persistence.customer_repository import SqlAlchemyCustomerRepository


def _build_customer(
    *, email: str = "cliente@example.com", identification: str = "ID-ADDR-0001"
) -> Customer:
    return Customer.create(
        name=Name("Cliente de Prueba"),
        identification=Identification(identification),
        age=Age(40),
        email=Email(email),
    )


def _build_address(*, customer_id: CustomerId, postal_code: str = "110111") -> Address:
    return Address.create(
        customer_id=customer_id,
        country=Country("Colombia"),
        state=State("Bogotá D.C."),
        city=City("Bogotá"),
        street_address=StreetAddress("Calle 123 #45-67"),
        postal_code=PostalCode(postal_code),
    )


def _persist_customer(db_session: Session) -> Customer:
    customer = _build_customer()
    SqlAlchemyCustomerRepository(db_session).add(customer)
    db_session.commit()
    return customer


def test_add_and_get_by_id_round_trips_address(db_session: Session) -> None:
    customer = _persist_customer(db_session)
    repository = SqlAlchemyAddressRepository(db_session)
    address = _build_address(customer_id=customer.id)

    repository.add(address)
    db_session.commit()

    found = repository.get_by_id(address.id)

    assert found is not None
    assert found.customer_id == customer.id
    assert found.status is EntityStatus.ACTIVE
    assert address.created_at is not None
    assert address.updated_at is not None


def test_add_raises_integrity_error_for_unknown_customer_foreign_key(
    db_session: Session,
) -> None:
    """`FOREIGN KEY addresses.customer_id -> customers.id` como red de seguridad real.

    A diferencia de `email`/`identification` (traducidas a excepciones de
    dominio en `customer_repository.py`), `AddressRepository.add()` no
    traduce `IntegrityError`: en el flujo normal, `CreateAddress` (Fase 2)
    ya verifica la existencia del cliente antes de llegar aquí, así que
    esta violación solo puede alcanzarse insertando directamente contra el
    repositorio, como hace este test.
    """
    repository = SqlAlchemyAddressRepository(db_session)
    address = _build_address(customer_id=CustomerId(uuid.uuid4()))

    with pytest.raises(IntegrityError):
        repository.add(address)


def test_get_by_id_excludes_deleted_addresses(db_session: Session) -> None:
    customer = _persist_customer(db_session)
    repository = SqlAlchemyAddressRepository(db_session)
    address = _build_address(customer_id=customer.id)
    repository.add(address)
    db_session.commit()

    address.mark_deleted()
    repository.update(address)
    db_session.commit()

    assert repository.get_by_id(address.id) is None


def test_list_by_customer_excludes_deleted_addresses_by_default(db_session: Session) -> None:
    customer = _persist_customer(db_session)
    repository = SqlAlchemyAddressRepository(db_session)
    active = _build_address(customer_id=customer.id, postal_code="110111")
    deleted = _build_address(customer_id=customer.id, postal_code="110222")
    repository.add(active)
    repository.add(deleted)
    db_session.commit()

    deleted.mark_deleted()
    repository.update(deleted)
    db_session.commit()

    addresses = repository.list_by_customer(customer.id)

    assert [a.id for a in addresses] == [active.id]


def test_list_by_customer_includes_deleted_when_requested(db_session: Session) -> None:
    customer = _persist_customer(db_session)
    repository = SqlAlchemyAddressRepository(db_session)
    active = _build_address(customer_id=customer.id, postal_code="110111")
    deleted = _build_address(customer_id=customer.id, postal_code="110222")
    repository.add(active)
    repository.add(deleted)
    db_session.commit()

    deleted.mark_deleted()
    repository.update(deleted)
    db_session.commit()

    addresses = repository.list_by_customer(customer.id, include_deleted=True)

    assert {a.id for a in addresses} == {active.id, deleted.id}


def test_count_active_by_customer_counts_only_active_addresses(db_session: Session) -> None:
    customer = _persist_customer(db_session)
    repository = SqlAlchemyAddressRepository(db_session)
    addresses = [_build_address(customer_id=customer.id, postal_code=f"11011{i}") for i in range(5)]
    for address in addresses:
        repository.add(address)
    db_session.commit()

    for address in addresses[:2]:
        address.mark_deleted()
        repository.update(address)
    db_session.commit()

    assert repository.count_active_by_customer(customer.id) == 3


def test_mark_all_deleted_by_customer_deletes_only_active_addresses(db_session: Session) -> None:
    customer = _persist_customer(db_session)
    repository = SqlAlchemyAddressRepository(db_session)
    first = _build_address(customer_id=customer.id, postal_code="110111")
    second = _build_address(customer_id=customer.id, postal_code="110222")
    repository.add(first)
    repository.add(second)
    db_session.commit()

    repository.mark_all_deleted_by_customer(customer.id)
    db_session.commit()

    remaining = repository.list_by_customer(customer.id, include_deleted=True)
    assert all(address.status is EntityStatus.DELETED for address in remaining)
    assert repository.count_active_by_customer(customer.id) == 0
