"""Pruebas de integración de `SqlAlchemyCustomerRepository` contra Postgres real.

Referencias: `specs/customers/implementation-plan.md` §8.1,
`specs/customers/plan.md` §6.2/§1.4. Cubre:

- `ux_customers_email`/`ux_customers_identification` como red de seguridad
  real de base de datos (no solo la validación de la capa de aplicación):
  se insertan dos clientes duplicados **directamente vía el repositorio**,
  sin pasar por `CreateCustomer` (que ya evita llegar a la constraint en el
  camino feliz).
- `get_by_id_for_update` adquiere un bloqueo real (`SELECT ... FOR UPDATE`)
  verificado por comportamiento de bloqueo entre dos sesiones concurrentes.
- Filtrado por `status <> 'DELETED'` en `get_by_id`, `find_by_email`,
  `find_by_identification` y `list_paginated`.
"""

from __future__ import annotations

import threading
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy.orm import Session

from customers.domain.customer.entities import Customer
from customers.domain.customer.exceptions import (
    DuplicateEmailError,
    DuplicateIdentificationError,
)
from customers.domain.customer.value_objects import Age, CustomerId, Email, Identification, Name
from customers.domain.shared.status import EntityStatus
from customers.infrastructure.persistence.customer_repository import SqlAlchemyCustomerRepository


def _build_customer(*, email: str = "ana@example.com", identification: str = "ID-0001") -> Customer:
    return Customer.create(
        name=Name("Ana Pérez"),
        identification=Identification(identification),
        age=Age(30),
        email=Email(email),
    )


def test_add_and_get_by_id_round_trips_customer(db_session: Session) -> None:
    repository = SqlAlchemyCustomerRepository(db_session)
    customer = _build_customer()

    repository.add(customer)
    db_session.commit()

    found = repository.get_by_id(customer.id)

    assert found is not None
    assert found.id == customer.id
    assert found.email.value == "ana@example.com"
    assert found.status is EntityStatus.ACTIVE
    assert customer.created_at is not None
    assert customer.updated_at is not None


def test_add_raises_duplicate_email_error_on_real_constraint_violation(
    db_session: Session,
) -> None:
    repository = SqlAlchemyCustomerRepository(db_session)
    first = _build_customer(email="duplicado@example.com", identification="ID-0001")
    repository.add(first)
    db_session.commit()

    second = _build_customer(email="duplicado@example.com", identification="ID-0002")

    with pytest.raises(DuplicateEmailError):
        repository.add(second)


def test_add_raises_duplicate_identification_error_on_real_constraint_violation(
    db_session: Session,
) -> None:
    repository = SqlAlchemyCustomerRepository(db_session)
    first = _build_customer(email="uno@example.com", identification="ID-DUP")
    repository.add(first)
    db_session.commit()

    second = _build_customer(email="dos@example.com", identification="ID-DUP")

    with pytest.raises(DuplicateIdentificationError):
        repository.add(second)


def test_get_by_id_excludes_deleted_customers(db_session: Session) -> None:
    repository = SqlAlchemyCustomerRepository(db_session)
    customer = _build_customer()
    repository.add(customer)
    db_session.commit()

    customer.status = EntityStatus.DELETED
    repository.update(customer)
    db_session.commit()

    assert repository.get_by_id(customer.id) is None


def test_find_by_email_excludes_deleted_customers(db_session: Session) -> None:
    repository = SqlAlchemyCustomerRepository(db_session)
    customer = _build_customer(email="eliminado@example.com")
    repository.add(customer)
    db_session.commit()

    customer.status = EntityStatus.DELETED
    repository.update(customer)
    db_session.commit()

    assert repository.find_by_email(Email("eliminado@example.com")) is None


def test_find_by_identification_excludes_deleted_customers(db_session: Session) -> None:
    repository = SqlAlchemyCustomerRepository(db_session)
    customer = _build_customer(identification="ID-DELETED")
    repository.add(customer)
    db_session.commit()

    customer.status = EntityStatus.DELETED
    repository.update(customer)
    db_session.commit()

    assert repository.find_by_identification(Identification("ID-DELETED")) is None


def test_list_paginated_excludes_deleted_customers(db_session: Session) -> None:
    repository = SqlAlchemyCustomerRepository(db_session)
    active = _build_customer(email="activo@example.com", identification="ID-ACTIVE")
    deleted = _build_customer(email="borrado@example.com", identification="ID-DELETED-2")
    repository.add(active)
    repository.add(deleted)
    db_session.commit()

    deleted.status = EntityStatus.DELETED
    repository.update(deleted)
    db_session.commit()

    customers, total = repository.list_paginated(page=1, page_size=20)

    assert total == 1
    assert [c.id for c in customers] == [active.id]


def test_get_by_id_for_update_blocks_concurrent_readers(
    make_session: Callable[[], Session],
) -> None:
    """Verifica el bloqueo pesimista (`SELECT ... FOR UPDATE`, `plan.md` §1.4).

    Una primera sesión adquiere el bloqueo y lo retiene; una segunda sesión
    que intenta `get_by_id_for_update` sobre la misma fila debe quedar
    bloqueada hasta que la primera libera la transacción (`rollback`).
    """
    setup_session = make_session()
    customer = _build_customer(email="lock@example.com", identification="ID-LOCK")
    SqlAlchemyCustomerRepository(setup_session).add(customer)
    setup_session.commit()

    lock_acquired = threading.Event()
    release_lock = threading.Event()
    second_call_finished = threading.Event()

    def hold_lock() -> None:
        session = make_session()
        repository = SqlAlchemyCustomerRepository(session)
        repository.get_by_id_for_update(customer.id)
        lock_acquired.set()
        release_lock.wait(timeout=5)
        session.rollback()

    def try_lock() -> None:
        lock_acquired.wait(timeout=5)
        session = make_session()
        repository = SqlAlchemyCustomerRepository(session)
        repository.get_by_id_for_update(customer.id)
        second_call_finished.set()
        session.rollback()

    with ThreadPoolExecutor(max_workers=2) as executor:
        holder = executor.submit(hold_lock)
        waiter = executor.submit(try_lock)

        lock_acquired.wait(timeout=5)
        # Mientras `hold_lock` no libera la fila, `try_lock` debe seguir
        # bloqueada intentando adquirir el mismo `FOR UPDATE`.
        finished_while_locked = second_call_finished.wait(timeout=0.5)
        assert finished_while_locked is False

        release_lock.set()
        holder.result(timeout=5)
        waiter.result(timeout=5)

    assert second_call_finished.is_set()


def test_get_by_id_for_update_returns_none_for_unknown_customer(db_session: Session) -> None:
    repository = SqlAlchemyCustomerRepository(db_session)
    assert repository.get_by_id_for_update(CustomerId(uuid.uuid4())) is None
