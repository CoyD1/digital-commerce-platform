from decimal import Decimal

import pytest_asyncio

from app.catalog.model import Product, ProductStatus
from app.users.model import User, UserStatus


@pytest_asyncio.fixture
async def order_data(db_session):
    buyer = User(
        name="Buyer",
        email="order-buyer@example.com",
        password_hash="unused-in-this-test",
        status=UserStatus.ACTIVE,
    )

    another_buyer = User(
        name="Another Buyer",
        email="another-order-buyer@example.com",
        password_hash="unused-in-this-test",
        status=UserStatus.ACTIVE,
    )

    products = [
        Product(
            title="Python Course",
            slug="order-python",
            description="Python course",
            price_amount=Decimal("1499.90"),
            status=ProductStatus.PUBLISHED,
        ),
        Product(
            title="SQL Course",
            slug="order-sql",
            description="SQL course",
            price_amount=Decimal("990.00"),
            status=ProductStatus.PUBLISHED,
        ),
    ]

    db_session.add_all([buyer, another_buyer, *products])
    await db_session.flush()

    return buyer, another_buyer, products
