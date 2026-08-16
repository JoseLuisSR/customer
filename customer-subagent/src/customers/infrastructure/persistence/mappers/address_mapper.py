from __future__ import annotations

from customers.domain.entities.address import Address
from customers.infrastructure.persistence.models.address_model import AddressModel


class AddressMapper:
    """Convierte entre la entidad de dominio Address y el modelo ORM
    AddressModel, para que el dominio nunca dependa de SQLAlchemy."""

    @staticmethod
    def to_entity(model: AddressModel) -> Address:
        return Address(
            id=model.id,
            customer_id=model.customer_id,
            country=model.country,
            state=model.state,
            city=model.city,
            postal_code=model.postal_code,
            address_line=model.address_line,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )

    @staticmethod
    def to_new_model(address: Address) -> AddressModel:
        return AddressModel(
            customer_id=address.customer_id,
            country=address.country,
            state=address.state,
            city=address.city,
            postal_code=address.postal_code,
            address_line=address.address_line,
        )

    @staticmethod
    def apply_to_model(address: Address, model: AddressModel) -> None:
        model.country = address.country
        model.state = address.state
        model.city = address.city
        model.postal_code = address.postal_code
        model.address_line = address.address_line
        model.deleted_at = address.deleted_at
