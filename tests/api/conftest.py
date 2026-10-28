import httpx
import pytest_asyncio

from app.db.session import get_session
from app.main import app


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as test_client:
            yield test_client

    finally:
        app.dependency_overrides.pop(get_session, None)
