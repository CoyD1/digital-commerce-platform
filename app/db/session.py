from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import settings


engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
)

session_factory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)

async def get_session():
    async with session_factory() as session:
        yield session