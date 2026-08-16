"""Estados funcionales compartidos por las entidades del dominio.

`Customer` y `Address` comparten el mismo catálogo mínimo de estados
(`ACTIVE`/`DELETED`, decisión Q-003, ver `specs/customers/plan.md` §7.3).
Se modela como `Enum` de cadenas en el dominio; la capa de persistencia
(Fase 3) lo mapea a `VARCHAR` + `CHECK` (no `ENUM` nativo de Postgres) para
facilitar ampliar el catálogo en el futuro sin migrar el tipo de columna.
"""

from __future__ import annotations

from enum import StrEnum


class EntityStatus(StrEnum):
    """Estado funcional de `Customer`/`Address`."""

    ACTIVE = "ACTIVE"
    DELETED = "DELETED"
