"""Códigos funcionales `ERR-00X` usados en `OperationResult.errors[].code`.

Los códigos `VAL-00X` de validación de formato de campo (VAL-001, VAL-003,
VAL-004, VAL-005, VAL-009) ya los produce cada value object de dominio
(`domain/*/value_objects.py`) a través de su método `validate()`. Este
módulo centraliza, en un único lugar, los códigos `ERR-00X` que construye
la capa de aplicación para fallos de una operación completa (no de un
campo puntual: duplicados, existencia, límites, pertenencia), siguiendo la
tabla de `specs/customers/plan.md` §2.4.

`ERR-008` es provisional (ver `specs/customers/implementation-plan.md` §11,
punto 1, y `specs/customers/plan.md` §2.4): identificación duplicada,
todavía sin código formal en `specs/customers/spec.md`. Centralizar estas
constantes minimiza el costo de renombrarlas si el spec funcional se
actualiza con códigos definitivos distintos.
"""

from __future__ import annotations

ERR_DUPLICATE_EMAIL = "ERR-002"
ERR_CUSTOMER_NOT_FOUND = "ERR-003"
ERR_ADDRESS_NOT_FOUND = "ERR-004"
ERR_MAX_ADDRESSES_EXCEEDED = "ERR-005"
ERR_ADDRESS_CUSTOMER_MISMATCH = "ERR-006"
ERR_DUPLICATE_IDENTIFICATION = "ERR-008"  # provisional, ver docstring del módulo
