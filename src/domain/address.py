import uuid


class Address:
    __id: uuid.UUID
    __customer_id: uuid.UUID
    __country: str
    __state: str
    __city: str
    __address: str
    __postal_code: str

    def __init__(
        self,
        id: uuid.UUID,
        customer_id: uuid.UUID,
        country: str,
        state: str,
        city: str,
        address: str,
        postal_code: str,
    ):
        self.__id = id
        self.__customer_id = customer_id
        self.__country = country
        self.__state = state
        self.__city = city
        self.__address = address
        self.__postal_code = postal_code

    @classmethod
    def create(
        cls,
        customer_id: uuid.UUID,
        country: str,
        state: str,
        city: str,
        address: str,
        postal_code: str,
    ) -> "Address":
        return cls(
            uuid.uuid4(), customer_id, country, state, city, address, postal_code
        )

    @classmethod
    def restore(
        cls,
        id: uuid.UUID,
        customer_id: uuid.UUID,
        country: str,
        state: str,
        city: str,
        address: str,
        postal_code: str,
    ) -> "Address":
        return cls(id, customer_id, country, state, city, address, postal_code)

    @property
    def id(self):
        return self.__id

    @property
    def customer_id(self):
        return self.__customer_id

    @property
    def country(self) -> str:
        return self.__country

    @country.setter
    def country(self, country: str):
        self.__country = country

    @property
    def state(self) -> str:
        return self.__state

    @state.setter
    def state(self, state: str):
        self.__state = state

    @property
    def city(self) -> str:
        return self.__city

    @city.setter
    def city(self, city: str):
        self.__city = city

    @property
    def address(self) -> str:
        return self.__address

    @address.setter
    def address(self, address: str):
        self.__address = address

    @property
    def postal_code(self) -> str:
        return self.__postal_code

    @postal_code.setter
    def postal_code(self, postal_code: str):
        self.__postal_code = postal_code
