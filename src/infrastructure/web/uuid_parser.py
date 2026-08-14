import uuid

from src.exception.customer_exception import InvalidUUIDError


def parse_uuid(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError, TypeError) as error:
        raise InvalidUUIDError(value) from error
