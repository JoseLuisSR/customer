import uuid


class CustomerNotFoundError(Exception):
    def __init__(self, id: uuid.UUID):
        self.id = id
        super().__init__(f"The customer with id {id} is not found.")


class InvalidUUIDError(Exception):
    def __init__(self, value: str):
        self.value = value
        super().__init__(f"UUID is invalid: {value}")


class CustomerWithIDAlreadyExistsError(Exception):
    def __init__(self, id: uuid.UUID):
        self.id = id
        super().__init__(f"The customer with id {id} already exists.")


class PersistenceUnavailableError(Exception):
    def __init__(self):
        super().__init__("The database is not available.")
