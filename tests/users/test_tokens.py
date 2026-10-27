from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.config import settings
from app.core.security import (
    create_access_token,
    InvalidAccessTokenError,
    decode_access_token,
)


def test_create_access_token_contains_user_and_expiration():
    before = int(datetime.now(timezone.utc).timestamp())

    token = create_access_token(user_id=42)

    after = int(datetime.now(timezone.utc).timestamp())

    payload = jwt.decode(
        token,
        settings.jwt_secret_key.get_secret_value(),
        algorithms=["HS256"],
        options={"require": ["sub", "iat", "exp"]},
    )

    assert payload["sub"] == "42"
    assert before <= payload["iat"] <= after

    expected_lifetime = settings.access_token_expire_minutes * 60

    assert payload["exp"] - payload["iat"] == expected_lifetime

def test_decode_access_token_returns_user_id():
    token = create_access_token(user_id=42)

    user_id = decode_access_token(token)

    assert user_id == 42

def test_decode_access_token_rejects_expired_token():
    now = datetime.now(timezone.utc)

    token = jwt.encode(
        {
            "sub" : "42",
            "iat": now - timedelta(minutes=20),
            "exp": now - timedelta(minutes=5),
        },
        settings.jwt_secret_key.get_secret_value(),
        algorithm="HS256",
    )

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(token)

def test_decode_access_token_rejects_wrong_signature():
    now = datetime.now(timezone.utc)

    token = jwt.encode(
        {
            "sub": "42",
            "iat": now,
            "exp": now + timedelta(minutes=15),
        },
        "different-test-signing-key-with-at-least-32-characters",
        algorithm="HS256",
    )

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(token)

@pytest.mark.parametrize("subject", ["abc", "", "0", "-1"])
def test_decode_access_token_rejects_invalid_user_id(subject):
    now = datetime.now(timezone.utc)

    token = jwt.encode(
        {
            "sub": subject,
            "iat": now,
            "exp": now + timedelta(minutes=15),
        },
        settings.jwt_secret_key.get_secret_value(),
        algorithm="HS256",
    )

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(token)

@pytest.mark.parametrize("missing_claim", ["sub", "iat", "exp"])
def test_decode_access_token_rejects_missing_claim(missing_claim):
    now = datetime.now(timezone.utc)

    payload = {
        "sub": "42",
        "iat": now,
        "exp": now + timedelta(minutes=15),
    }
    del payload[missing_claim]

    token = jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm="HS256",
    )

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(token)