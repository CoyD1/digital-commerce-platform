from app.core.security import hash_password, verify_password
from app.users.model import User, UserStatus
from app.users.repository import UserRepository
from app.users.schemas import UserCreate


class EmailAlreadyExistsError(Exception):
    pass

class InvalidCredentialsError(Exception):
    pass

class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def register(self, data: UserCreate) -> User:
        existing_user = await self._repository.get_by_email(
                str(data.email)
            )

        if existing_user is not None:
            raise EmailAlreadyExistsError(
                "User with this email already exists"
            )

        user = User(
            name=data.name,
            email=str(data.email),
            status=UserStatus.ACTIVE,
            password_hash=hash_password(data.password),
        )

        return await self._repository.create(user)
    
    async def authenticate(self, email: str, password: str):
        user = await self._repository.get_by_email(email)

        if user is None:
            raise InvalidCredentialsError("Invalid email or password")

        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")

        if user.status != UserStatus.ACTIVE:
            raise InvalidCredentialsError("Invalid email or password")

        return user
