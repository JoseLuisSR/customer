import uuid


class CustomerNotFoundException(Exception):
    def __init__(self, id: uuid.UUID):
        self.id = id
        super().__init__(f"The customer with id {id} is not found.")


class InvalidUUIDException(Exception):
    def __init__(self, value: str):
        self.value = value
        super().__init__(f"UUID is invalid: {value}")
