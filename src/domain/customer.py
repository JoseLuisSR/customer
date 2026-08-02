import uuid


class Customer:
    __id: uuid.UUID
    __name: str
    __age: int
    __email: str

    def __init__(self, id: uuid.UUID, name: str, age: int, email: str):
        self.__id = id
        self.__name = name
        self.__age = age
        self.__email = email

    @classmethod
    def create(cls, name: str, age: int, email: str) -> "Customer":
        return cls(uuid.uuid4(), name, age, email)

    @classmethod
    def restore(cls, id: uuid.UUID, name: str, age: int, email: str) -> "Customer":
        return cls(id, name, age, email)

    @property
    def id(self):
        return self.__id

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, name: str):
        self.__name = name

    @property
    def email(self) -> str:
        return self.__email

    @email.setter
    def email(self, email: str):
        self.__email = email

    @property
    def age(self) -> int:
        return self.__age

    @age.setter
    def age(self, age: int):
        self.__age = age
