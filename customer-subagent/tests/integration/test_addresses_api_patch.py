from customers.infrastructure.persistence.repositories import (
    SQLAlchemyAddressRepository,
)


def test_patch_address_updates_only_provided_fields(
    client, create_customer, create_address
):
    customer = create_customer().get_json()
    created = create_address(customer["id"]).get_json()

    response = client.patch(
        f"/customers/{customer['id']}/addresses/{created['id']}",
        json={"city": "Bogota"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["city"] == "Bogota"
    assert body["country"] == created["country"]
    assert body["postalcode"] == created["postalcode"]


def test_patch_address_returns_404_when_customer_does_not_exist(client):
    response = client.patch("/customers/999999/addresses/1", json={"city": "Bogota"})

    assert response.status_code == 404
    assert response.get_json() == {"error": "customer not found"}


def test_patch_address_returns_404_when_address_does_not_exist(client, create_customer):
    customer = create_customer().get_json()

    response = client.patch(
        f"/customers/{customer['id']}/addresses/999999", json={"city": "Bogota"}
    )

    assert response.status_code == 404
    assert response.get_json() == {"error": "address not found"}


def test_patch_address_with_no_fields_returns_400(
    client, create_customer, create_address
):
    customer = create_customer().get_json()
    created = create_address(customer["id"]).get_json()

    response = client.patch(
        f"/customers/{customer['id']}/addresses/{created['id']}", json={}
    )

    assert response.status_code == 400
    assert response.get_json()["details"]["body"] == "no fields to update"


def test_patch_address_with_mismatched_body_id_returns_400(
    client, create_customer, create_address
):
    customer = create_customer().get_json()
    created = create_address(customer["id"]).get_json()

    response = client.patch(
        f"/customers/{customer['id']}/addresses/{created['id']}",
        json={"id": created["id"] + 1, "city": "Bogota"},
    )

    assert response.status_code == 400
    assert response.get_json()["details"]["id"]


def test_patch_address_with_non_integer_body_id_returns_400(
    client, create_customer, create_address
):
    customer = create_customer().get_json()
    created = create_address(customer["id"]).get_json()

    response = client.patch(
        f"/customers/{customer['id']}/addresses/{created['id']}",
        json={"id": "not-an-int", "city": "Bogota"},
    )

    assert response.status_code == 400
    assert response.get_json()["details"]["id"]


def test_patch_address_with_invalid_field_returns_400(
    client, create_customer, create_address
):
    customer = create_customer().get_json()
    created = create_address(customer["id"]).get_json()

    response = client.patch(
        f"/customers/{customer['id']}/addresses/{created['id']}",
        json={"city": ""},
    )

    assert response.status_code == 400
    assert response.get_json()["details"]["city"]


def test_patch_address_returns_404_when_belongs_to_another_customer(
    client, create_customer, create_address
):
    customer_a = create_customer().get_json()
    customer_b = create_customer(email="grace@example.com").get_json()
    address_of_b = create_address(customer_b["id"]).get_json()

    response = client.patch(
        f"/customers/{customer_a['id']}/addresses/{address_of_b['id']}",
        json={"city": "Should Not Work"},
    )

    assert response.status_code == 404
    assert response.get_json() == {"error": "address not found"}


def test_patch_address_unexpected_error_returns_500_without_leaking_details(
    client, create_customer, create_address, monkeypatch
):
    customer = create_customer().get_json()
    created = create_address(customer["id"]).get_json()

    def _raise(self, address):
        raise RuntimeError("boom: connection lost to internal db host")

    monkeypatch.setattr(SQLAlchemyAddressRepository, "update", _raise)

    response = client.patch(
        f"/customers/{customer['id']}/addresses/{created['id']}",
        json={"city": "Bogota"},
    )

    assert response.status_code == 500
    body = response.get_json()
    assert body == {"error": "internal server error"}
    assert "boom" not in response.get_data(as_text=True)
