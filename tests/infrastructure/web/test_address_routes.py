import uuid
from http import HTTPStatus

import pytest
from flask.testing import FlaskClient

# Every test in this module needs a live Postgres connection (see
# tests/conftest.py::app for the requirements). The routes instantiate
# DatabaseAddressRepository()/DatabaseCustomerRepository() at module level
# without dependency injection, so there is no way to exercise them against
# a mocked repository without changing the architecture (out of scope here).
pytestmark = pytest.mark.usefixtures("app")

ADDRESS_PAYLOAD = {
    "country": "Colombia",
    "state": "Bogota D.C.",
    "city": "Bogota",
    "address": "Cra 1 # 2-3",
    "postal-code": "110111",
}


def _addresses_url(customer_id: uuid.UUID) -> str:
    return f"/api/v1/customers/{customer_id}/addresses"


class TestCreate:
    def test_returns_201_with_the_created_address(
        self, client: FlaskClient, customer_id: uuid.UUID
    ):
        response = client.post(_addresses_url(customer_id), json=ADDRESS_PAYLOAD)

        assert response.status_code == HTTPStatus.CREATED
        body = response.get_json()
        assert "postal-code" in body
        assert "postal_code" not in body
        assert body["postal-code"] == "110111"
        assert body["country"] == "Colombia"
        assert uuid.UUID(body["id"])

    def test_returns_409_when_the_limit_of_5_addresses_is_exceeded(
        self, client: FlaskClient, customer_id: uuid.UUID
    ):
        for _ in range(5):
            response = client.post(_addresses_url(customer_id), json=ADDRESS_PAYLOAD)
            assert response.status_code == HTTPStatus.CREATED

        response = client.post(_addresses_url(customer_id), json=ADDRESS_PAYLOAD)

        assert response.status_code == HTTPStatus.CONFLICT


class TestGetById:
    def test_returns_200_with_the_address(
        self, client: FlaskClient, customer_id: uuid.UUID
    ):
        created = client.post(
            _addresses_url(customer_id), json=ADDRESS_PAYLOAD
        ).get_json()

        response = client.get(f"{_addresses_url(customer_id)}/{created['id']}")

        assert response.status_code == HTTPStatus.OK
        assert response.get_json()["id"] == created["id"]

    def test_returns_404_when_the_address_does_not_exist(
        self, client: FlaskClient, customer_id: uuid.UUID
    ):
        response = client.get(f"{_addresses_url(customer_id)}/{uuid.uuid4()}")

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_returns_400_for_an_invalid_uuid(
        self, client: FlaskClient, customer_id: uuid.UUID
    ):
        response = client.get(f"{_addresses_url(customer_id)}/not-a-uuid")

        assert response.status_code == HTTPStatus.BAD_REQUEST


class TestGetAll:
    def test_returns_200_with_the_list_of_addresses(
        self, client: FlaskClient, customer_id: uuid.UUID
    ):
        client.post(_addresses_url(customer_id), json=ADDRESS_PAYLOAD)
        client.post(
            _addresses_url(customer_id), json={**ADDRESS_PAYLOAD, "city": "Medellin"}
        )

        response = client.get(f"{_addresses_url(customer_id)}/all")

        assert response.status_code == HTTPStatus.OK
        body = response.get_json()
        assert len(body) == 2
        assert all("postal-code" in item for item in body)


class TestUpdatePartial:
    def test_returns_200_and_only_updates_the_sent_fields(
        self, client: FlaskClient, customer_id: uuid.UUID
    ):
        created = client.post(
            _addresses_url(customer_id), json=ADDRESS_PAYLOAD
        ).get_json()

        response = client.patch(
            f"{_addresses_url(customer_id)}/{created['id']}", json={"city": "Medellin"}
        )

        assert response.status_code == HTTPStatus.OK
        body = response.get_json()
        assert body["city"] == "Medellin"
        assert body["country"] == ADDRESS_PAYLOAD["country"]
        assert body["postal-code"] == ADDRESS_PAYLOAD["postal-code"]


class TestReplace:
    def test_returns_200_when_replacing_an_existing_address(
        self, client: FlaskClient, customer_id: uuid.UUID
    ):
        created = client.post(
            _addresses_url(customer_id), json=ADDRESS_PAYLOAD
        ).get_json()
        replacement = {**ADDRESS_PAYLOAD, "city": "Cali"}

        response = client.put(
            f"{_addresses_url(customer_id)}/{created['id']}", json=replacement
        )

        assert response.status_code == HTTPStatus.OK
        assert response.get_json()["city"] == "Cali"

    def test_returns_201_when_the_upsert_creates_a_new_address(
        self, client: FlaskClient, customer_id: uuid.UUID
    ):
        new_id = uuid.uuid4()

        response = client.put(
            f"{_addresses_url(customer_id)}/{new_id}", json=ADDRESS_PAYLOAD
        )

        assert response.status_code == HTTPStatus.CREATED
        assert response.get_json()["id"] == str(new_id)

    def test_returns_409_when_the_upsert_creation_exceeds_the_limit(
        self, client: FlaskClient, customer_id: uuid.UUID
    ):
        for _ in range(5):
            response = client.post(_addresses_url(customer_id), json=ADDRESS_PAYLOAD)
            assert response.status_code == HTTPStatus.CREATED

        response = client.put(
            f"{_addresses_url(customer_id)}/{uuid.uuid4()}", json=ADDRESS_PAYLOAD
        )

        assert response.status_code == HTTPStatus.CONFLICT


class TestDelete:
    def test_returns_204_and_then_404_on_a_subsequent_get(
        self, client: FlaskClient, customer_id: uuid.UUID
    ):
        created = client.post(
            _addresses_url(customer_id), json=ADDRESS_PAYLOAD
        ).get_json()
        address_url = f"{_addresses_url(customer_id)}/{created['id']}"

        delete_response = client.delete(address_url)
        assert delete_response.status_code == HTTPStatus.NO_CONTENT

        get_response = client.get(address_url)
        assert get_response.status_code == HTTPStatus.NOT_FOUND
