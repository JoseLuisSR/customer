class CustomerError(Exception):
    """Clase base de las excepciones del dominio Customer."""


class CustomerValidationError(CustomerError):
    def __init__(self, field: str, message: str) -> None:
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class CustomerNotFoundError(CustomerError):
    def __init__(self, customer_id: int) -> None:
        self.customer_id = customer_id
        super().__init__(f"customer {customer_id} not found")


class CustomerAlreadyDeletedError(CustomerError):
    def __init__(self, customer_id: int) -> None:
        self.customer_id = customer_id
        super().__init__(f"customer {customer_id} already deleted")


class CustomerEmailAlreadyExistsError(CustomerError):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"email {email} already exists")


class AddressError(Exception):
    """Clase base de las excepciones del dominio Address."""


class AddressValidationError(AddressError):
    def __init__(self, field: str, message: str) -> None:
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class AddressNotFoundError(AddressError):
    def __init__(self, address_id: int) -> None:
        self.address_id = address_id
        super().__init__(f"address {address_id} not found")


class AddressAlreadyDeletedError(AddressError):
    def __init__(self, address_id: int) -> None:
        self.address_id = address_id
        super().__init__(f"address {address_id} already deleted")
