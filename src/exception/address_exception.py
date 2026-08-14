import uuid


class AddressNotFoundError(Exception):
    def __init__(self, customer_id: uuid.UUID, address_id: uuid.UUID):
        self.customer_id = customer_id
        self.address_id = address_id
        super().__init__(
            f"The address with id {address_id} for customer with id {customer_id} is not found."
        )


class MaxAddressesPerCustomerError(Exception):
    def __init__(self, customer_id: uuid.UUID, limit: int = 5):
        self.customer_id = customer_id
        self.limit = limit
        super().__init__(
            f"The customer with id {customer_id} has already reached the maximum of {limit} addresses."
        )
