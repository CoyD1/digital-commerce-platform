from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.model import User


class UserRepository:

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: int) -> User | None:
        statement = select(User).where(User.id == user_id)

        result = await self._session.execute(statement)

        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)

        result = await self._session.execute(statement)

        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self._session.add(user)

        await self._session.flush()
        await self._session.refresh(user)

        return user