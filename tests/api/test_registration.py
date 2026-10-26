import pytest


@pytest.mark.asyncio
async def test_register_returns_user_without_password(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Alice",
            "email": "api-registration@example.com",
            "password": "example-password",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["id"] > 0
    assert body["name"] == "Alice"
    assert body["email"] == "api-registration@example.com"
    assert body["status"] == "ACTIVE"
    assert "password" not in body
    assert "password_hash" not in body


@pytest.mark.asyncio
async def test_register_returns_conflict_for_existing_email(client):
    registration = {
        "name": "Alice",
        "email": "api-duplicate@example.com",
        "password": "example-password",
    }

    first_response = await client.post(
        "/api/v1/auth/register",
        json=registration,
    )
    assert first_response.status_code == 201

    second_response = await client.post(
        "/api/v1/auth/register",
        json=registration,
    )

    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "Email already registered",
    }


@pytest.mark.asyncio
async def test_register_returns_validation_error_for_invalid_email(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Alice",
            "email": "invalid-email",
            "password": "example-password",
        },
    )

    assert response.status_code == 422

    errors = response.json()["detail"]

    assert any(
        error["loc"] == ["body", "email"]
        for error in errors
    )