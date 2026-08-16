from customers.infrastructure.persistence.repositories import (
    SQLAlchemyCustomerRepository,
)


def test_patch_customer_updates_only_provided_fields(client, create_customer):
    created = create_customer().get_json()

    response = client.patch(f"/customers/{created['id']}", json={"age": 31})

    assert response.status_code == 200
    body = response.get_json()
    assert body["age"] == 31
    assert body["name"] == created["name"]
    assert body["email"] == created["email"]


def test_patch_customer_returns_404_when_not_found(client):
    response = client.patch("/customers/999999", json={"age": 31})

    assert response.status_code == 404


def test_patch_customer_with_no_fields_returns_400(client, create_customer):
    created = create_customer().get_json()

    response = client.patch(f"/customers/{created['id']}", json={})

    assert response.status_code == 400
    assert response.get_json()["details"]["body"] == "no fields to update"


def test_patch_customer_with_mismatched_body_id_returns_400(client, create_customer):
    created = create_customer().get_json()

    response = client.patch(
        f"/customers/{created['id']}",
        json={"id": created["id"] + 1, "age": 31},
    )

    assert response.status_code == 400
    assert response.get_json()["details"]["id"]


def test_patch_customer_with_non_integer_body_id_returns_400(client, create_customer):
    created = create_customer().get_json()

    response = client.patch(
        f"/customers/{created['id']}", json={"id": "not-an-int", "age": 31}
    )

    assert response.status_code == 400
    assert response.get_json()["details"]["id"]


def test_patch_customer_with_invalid_field_returns_400(client, create_customer):
    created = create_customer().get_json()

    response = client.patch(f"/customers/{created['id']}", json={"age": -1})

    assert response.status_code == 400
    assert response.get_json()["details"]["age"]


def test_patch_customer_with_duplicate_email_returns_409(client, create_customer):
    create_customer(email="taken@example.com")
    other = create_customer(name="Grace Hopper", email="grace@example.com").get_json()

    response = client.patch(
        f"/customers/{other['id']}", json={"email": "taken@example.com"}
    )

    assert response.status_code == 409
    assert response.get_json()["error"] == "email already exists"


def test_patch_customer_unexpected_error_returns_500_without_leaking_details(
    client, create_customer, monkeypatch
):
    created = create_customer().get_json()

    def _raise(self, customer):
        raise RuntimeError("boom: connection lost to internal db host")

    monkeypatch.setattr(SQLAlchemyCustomerRepository, "update", _raise)

    response = client.patch(f"/customers/{created['id']}", json={"age": 31})

    assert response.status_code == 500
    body = response.get_json()
    assert body == {"error": "internal server error"}
    assert "boom" not in response.get_data(as_text=True)
