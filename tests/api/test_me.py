import pytest

from app.users.model import User, UserStatus


@pytest.mark.asyncio
async def test_me_returns_current_user(client):
    credentials = {
        "email": "me-api@example.com",
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

    registered_user = registration_response.json()

    login_response = await client.post(
        "/api/v1/auth/login",
        json=credentials,
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = await client.get(
        "/api/v1/users/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == registered_user["id"]
    assert body["email"] == registered_user["email"]
    assert "password" not in body
    assert "password_hash" not in body


@pytest.mark.asyncio
async def test_me_rejects_request_without_token(client):
    response = await client.get("/api/v1/users/me")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid authentication credentials",
    }
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.asyncio
async def test_me_rejects_invalid_token(client):
    response = await client.get(
        "/api/v1/users/me",
        headers={
            "Authorization": "Bearer not-a-valid-jwt",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid authentication credentials",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_status",
    [UserStatus.BLOCKED, UserStatus.DELETED],
)
async def test_me_rejects_inactive_user(
    client,
    db_session,
    user_status,
):
    credentials = {
        "email": "me-inactive@example.com",
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

    login_response = await client.post(
        "/api/v1/auth/login",
        json=credentials,
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    user = await db_session.get(User, user_id)
    assert user is not None

    user.status = user_status
    await db_session.flush()

    response = await client.get(
        "/api/v1/users/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid authentication credentials",
    }
