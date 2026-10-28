import pytest

from app.core.security import verify_password
from app.users.model import UserStatus
from app.users.repository import UserRepository
from app.users.schemas import UserCreate
from app.users.service import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    UserService,
)


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

    stored_user = await repository.get_by_email("duplicate-registration@example.com")

    assert stored_user is not None
    assert stored_user.name == "Alice"
    assert verify_password(
        first_registration.password,
        stored_user.password_hash,
    )


@pytest.mark.asyncio
async def test_authenticate_returns_user_for_valid_credentials(db_session):
    repository = UserRepository(db_session)
    service = UserService(repository)

    registration = UserCreate(
        name="Alice",
        email="login@example.com",
        password="example-password",
    )
    created_user = await service.register(registration)

    authenticated_user = await service.authenticate(
        email=str(registration.email),
        password=registration.password,
    )

    assert authenticated_user.id == created_user.id
    assert authenticated_user.email == created_user.email


@pytest.mark.asyncio
async def test_authenticate_rejects_unknown_email(db_session):
    repository = UserRepository(db_session)
    service = UserService(repository)

    with pytest.raises(InvalidCredentialsError):
        await service.authenticate(
            email="unknown@example.com",
            password="example-password",
        )


@pytest.mark.asyncio
async def test_authenticate_rejects_wrong_password(db_session):
    repository = UserRepository(db_session)
    service = UserService(repository)

    await service.register(
        UserCreate(
            name="Alice",
            email="wrong-password@example.com",
            password="correct-password",
        )
    )

    with pytest.raises(InvalidCredentialsError):
        await service.authenticate(
            email="wrong-password@example.com",
            password="incorrect-password",
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_status",
    [UserStatus.BLOCKED, UserStatus.DELETED],
)
async def test_authenticate_rejects_inactive_user(db_session, user_status):
    repository = UserRepository(db_session)
    service = UserService(repository)

    user = await service.register(
        UserCreate(
            name="Alice",
            email="inactive@example.com",
            password="example-password",
        )
    )

    user.status = user_status
    await db_session.flush()

    with pytest.raises(InvalidCredentialsError):
        await service.authenticate(
            email="inactive@example.com",
            password="example-password",
        )
