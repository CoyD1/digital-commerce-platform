import pytest

from app.core.security import decode_access_token


@pytest.mark.asyncio
async def test_login_returns_access_token(client):
    credentials = {
        "email": "login-api@example.com",
        "password": "example-password",
    }

    registration_response = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Alice",
            **credentials,
        },
    )
    assert registration_response.status_code == 201

    user_id = registration_response.json()["id"]

    response = await client.post(
        "/api/v1/auth/login",
        json=credentials,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["token_type"] == "bearer"
    assert decode_access_token(body["access_token"]) == user_id

@pytest.mark.asyncio
async def test_login_rejects_wrong_password(client):
    registration_response = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Alice",
            "email": "login-wrong-password@example.com",
            "password": "example-password",
        },
    )
    assert registration_response.status_code == 201

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "login-wrong-password@example.com",
            "password": "incorrect-password",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid email or password",
    }
    assert response.headers["www-authenticate"] == "Bearer"