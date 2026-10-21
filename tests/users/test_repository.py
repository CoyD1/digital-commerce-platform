import pytest

from app.users.model import User, UserStatus
from app.users.repository import UserRepository

@pytest.mark.asyncio
async def test_get_by_id_returns_user(db_session):
    repository = UserRepository(db_session)

    user = User(
        name="Test User",
        email="by-id@example.com",
        status=UserStatus.ACTIVE,
        password_hash="test-hash",
    )

    created_user = await repository.create(user)

    result = await repository.get_by_id(created_user.id)

    assert result is not None
    assert result.id == created_user.id
    assert result.email == created_user.email

@pytest.mark.asyncio
async def test_get_by_id_returns_none(db_session):
    repository = UserRepository(db_session)

    result = await repository.get_by_id(9999999999999)

    assert result is None