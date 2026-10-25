import pytest

from sqlalchemy.exc import IntegrityError

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

@pytest.mark.asyncio
async def test_get_by_email_returns_user(db_session):
    repository = UserRepository(db_session)

    user = User(
        name="Email Test",
        email="by-email@example.com",
        status=UserStatus.ACTIVE,
        password_hash="test-hash",
    )
    created_user = await repository.create(user)

    result = await repository.get_by_email("by-email@example.com")

    assert result is not None
    assert result.id == created_user.id
    assert result.email == "by-email@example.com"


@pytest.mark.asyncio
async def test_get_by_email_returns_none(db_session):
    repository = UserRepository(db_session)

    result = await repository.get_by_email("missing@example.com")

    assert result is None

@pytest.mark.asyncio
async def test_create_rejects_duplicate_email(db_session):
    repository = UserRepository(db_session)

    first_user = User(
        name="First User",
        email="duplicate@example.com",
        status=UserStatus.ACTIVE,
        password_hash="test-hash",
    )
    await repository.create(first_user)

    second_user = User(
        name="Second User",
        email="duplicate@example.com",
        status=UserStatus.ACTIVE,
        password_hash="another-test-hash",
    )

    with pytest.raises(IntegrityError):
        await repository.create(second_user)

    await db_session.rollback()