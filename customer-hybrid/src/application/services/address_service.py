import uuid

from src.application.dto.address_dto import AddressPatchRqst, AddressRqst, AddressRsps
from src.application.repository.address_repository import AddressRepository
from src.domain.address import Address
from src.exception.address_exception import (
    AddressNotFoundError,
    MaxAddressesPerCustomerError,
)

MAX_ADDRESSES_PER_CUSTOMER = 5


class AddressService:
    def __init__(self, repository: AddressRepository):
        self.repository = repository

    @staticmethod
    def _to_rsps(address: Address) -> AddressRsps:
        # AddressRsps.postal_code only exposes the "postal-code" alias in its
        # synthesized constructor signature (dataclass_transform doesn't model
        # `populate_by_name=True`, and the bundled pydantic mypy plugin is not
        # usable with the mypy version pinned in this project — see design
        # notes). model_validate(..., from_attributes=True) reads the domain
        # entity's plain attributes by field name at runtime (populate_by_name
        # honors that fallback) while staying mypy-clean, so it's used instead
        # of keyword-argument construction for this DTO specifically.
        return AddressRsps.model_validate(address, from_attributes=True)

    def create(self, customer_id: uuid.UUID, address_rqst: AddressRqst) -> AddressRsps:
        if (
            self.repository.count_by_customer_id(customer_id)
            >= MAX_ADDRESSES_PER_CUSTOMER
        ):
            raise MaxAddressesPerCustomerError(customer_id)

        address: Address = Address.create(
            customer_id,
            address_rqst.country,
            address_rqst.state,
            address_rqst.city,
            address_rqst.address,
            address_rqst.postal_code,
        )
        self.repository.create(address)
        return self._to_rsps(address)

    def get_by_id(self, customer_id: uuid.UUID, address_id: uuid.UUID) -> AddressRsps:
        address: Address = self.repository.get_by_id(customer_id, address_id)
        return self._to_rsps(address)

    def get_all(self, customer_id: uuid.UUID) -> list[AddressRsps]:
        addresses = self.repository.get_all_by_customer_id(customer_id)
        return [self._to_rsps(address) for address in addresses]

    def update_partial(
        self,
        customer_id: uuid.UUID,
        address_id: uuid.UUID,
        patch_rqst: AddressPatchRqst,
    ) -> AddressRsps:
        address: Address = self.repository.get_by_id(customer_id, address_id)

        if patch_rqst.country is not None:
            address.country = patch_rqst.country
        if patch_rqst.state is not None:
            address.state = patch_rqst.state
        if patch_rqst.city is not None:
            address.city = patch_rqst.city
        if patch_rqst.address is not None:
            address.address = patch_rqst.address
        if patch_rqst.postal_code is not None:
            address.postal_code = patch_rqst.postal_code

        address_updated: Address = self.repository.update_partial(
            customer_id, address_id, address
        )
        return self._to_rsps(address_updated)

    def replace(
        self, customer_id: uuid.UUID, address_id: uuid.UUID, address_rqst: AddressRqst
    ) -> tuple[AddressRsps, bool]:
        # The upsert limit check must happen before calling repository.upsert,
        # so we need to know upfront whether this call will create a new row.
        # We probe existence via get_by_id/AddressNotFoundError instead of adding
        # an extra "exists" method to the port, reusing what the interface already
        # exposes. This is a best-effort check (see design notes: no locking in
        # this project, so a race between the check and the upsert is out of scope).
        will_create = False
        try:
            self.repository.get_by_id(customer_id, address_id)
        except AddressNotFoundError:
            will_create = True

        if (
            will_create
            and self.repository.count_by_customer_id(customer_id)
            >= MAX_ADDRESSES_PER_CUSTOMER
        ):
            raise MaxAddressesPerCustomerError(customer_id)

        address: Address = Address.restore(
            address_id,
            customer_id,
            address_rqst.country,
            address_rqst.state,
            address_rqst.city,
            address_rqst.address,
            address_rqst.postal_code,
        )
        address_result, created = self.repository.upsert(
            customer_id, address_id, address
        )
        return self._to_rsps(address_result), created

    def delete_by_id(self, customer_id: uuid.UUID, address_id: uuid.UUID) -> None:
        self.repository.delete_by_id(customer_id, address_id)
