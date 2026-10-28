from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

_password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _password_hasher.verify(password, password_hash)


def create_access_token(user_id: int) -> str:
    now = datetime.now(UTC)

    expires_at = now + timedelta(minutes=settings.access_token_expire_minutes)

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm="HS256",
    )


class InvalidAccessTokenError(Exception):
    pass


def decode_access_token(token: str) -> int:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=["HS256"],
            options={"require": ["sub", "iat", "exp"]},
        )

        user_id = int(payload["sub"])

        if user_id <= 0:
            raise ValueError("User ID must be positive")

    except (jwt.InvalidTokenError, ValueError, TypeError) as error:
        raise InvalidAccessTokenError("Invalid access token") from error

    return user_id
