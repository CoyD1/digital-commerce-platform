import asyncio
import os
import selectors
import sys

import pytest
import pytest_asyncio
from alembic.config import Config
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from alembic import command

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    raise RuntimeError(
        "Set TEST_DATABASE_URL to the commerce_test database"
    )

if make_url(TEST_DATABASE_URL).database != "commerce_test":
    raise RuntimeError(
        "Tests may run only against commerce_test"
    )

def pytest_asyncio_loop_factories(config, item):
    if sys.platform == "win32":
        return {
            "selector": lambda: asyncio.SelectorEventLoop(
                selectors.SelectSelector()
            )
        }

    return {"default": asyncio.new_event_loop}

@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    config = Config("alembic-test.ini")
    config.set_main_option(
        "sqlalchemy.url",
        TEST_DATABASE_URL.replace("%", "%%"),
    )
    command.upgrade(config, "head")

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
    )

    try:
        async with engine.connect() as connection:
            outer_transaction = await connection.begin()

            try:
                async with AsyncSession(
                    bind=connection,
                    expire_on_commit=False,
                    join_transaction_mode="create_savepoint",
                ) as session:
                    yield session

            finally:
                if outer_transaction.is_active:
                    await outer_transaction.rollback()

    finally:
        await engine.dispose()