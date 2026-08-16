from customers.infrastructure.persistence.repositories import (
    SQLAlchemyAddressRepository,
)


def test_create_address_returns_201(client, create_customer, create_address):
    customer = create_customer().get_json()

    response = create_address(customer["id"])

    assert response.status_code == 201
    body = response.get_json()
    assert body["country"] == "Colombia"
    assert body["state"] == "Meta"
    assert body["city"] == "Villavicencio"
    assert body["postalcode"] == "50001"
    assert body["address"] == "Calle 10 #5-20"
    assert isinstance(body["id"], int)


def test_create_address_with_malformed_json_returns_400(client, create_customer):
    customer = create_customer().get_json()

    response = client.post(
        f"/customers/{customer['id']}/addresses",
        data="not json",
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "validation failed"


def test_create_address_missing_field_returns_400(
    client, create_customer, create_address
):
    customer = create_customer().get_json()

    response = create_address(customer["id"], postalcode=None)

    assert response.status_code == 400
    body = response.get_json()
    assert body["error"] == "validation failed"
    assert "postalcode" in body["details"]


def test_create_address_invalid_field_returns_400(
    client, create_customer, create_address
):
    customer = create_customer().get_json()

    response = create_address(customer["id"], country="")

    assert response.status_code == 400
    assert response.get_json()["details"]["country"]


def test_create_address_returns_404_when_customer_does_not_exist(
    client, create_address
):
    response = create_address(999999)

    assert response.status_code == 404
    assert response.get_json() == {"error": "customer not found"}


def test_create_address_returns_404_when_customer_is_soft_deleted(
    client, create_customer, create_address
):
    customer = create_customer().get_json()
    client.delete(f"/customers/{customer['id']}")

    response = create_address(customer["id"])

    assert response.status_code == 404


def test_create_address_unexpected_error_returns_500_without_leaking_details(
    client, create_customer, monkeypatch
):
    customer = create_customer().get_json()

    def _raise(self, address):
        raise RuntimeError("boom: connection lost to internal db host")

    monkeypatch.setattr(SQLAlchemyAddressRepository, "add", _raise)

    response = client.post(
        f"/customers/{customer['id']}/addresses",
        json={
            "country": "Colombia",
            "state": "Meta",
            "city": "Villavicencio",
            "postalcode": "50001",
            "address": "Calle 10 #5-20",
        },
    )

    assert response.status_code == 500
    body = response.get_json()
    assert body == {"error": "internal server error"}
    assert "boom" not in response.get_data(as_text=True)
