import pytest

from app.core.security import verify_password
from app.users.model import UserStatus
from app.users.repository import UserRepository
from app.users.schemas import UserCreate
from app.users.service import EmailAlreadyExistsError, UserService


@pytest.mark.asyncio
async def test_register_creates_user_with_hashed_password(db_session):
    repository = UserRepository(db_session)
    service = UserService(repository)

    data = UserCreate(
        name="Alice",
        email="register@example.com",
        password="example-password",
    )

    user = await service.register(data)

    assert user.id is not None
    assert user.email == "register@example.com"
    assert user.status == UserStatus.ACTIVE
    assert user.password_hash != data.password
    assert verify_password(data.password, user.password_hash)

    stored_user = await repository.get_by_id(user.id)

    assert stored_user is not None
    assert stored_user.email == user.email

@pytest.mark.asyncio
async def test_register_rejects_existing_email(db_session):
    repository = UserRepository(db_session)
    service = UserService(repository)

    first_registration = UserCreate(
        name="Alice",
        email="duplicate-registration@example.com",
        password="first-password",
    )
    await service.register(first_registration)

    second_registration = UserCreate(
        name="Bob",
        email="duplicate-registration@example.com",
        password="second-password",
    )

    with pytest.raises(EmailAlreadyExistsError):
        await service.register(second_registration)

    stored_user = await repository.get_by_email(
        "duplicate-registration@example.com"
    )

    assert stored_user is not None
    assert stored_user.name == "Alice"
    assert verify_password(
        first_registration.password,
        stored_user.password_hash,
    )