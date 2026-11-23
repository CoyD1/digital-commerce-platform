import pytest
from sqlalchemy import select

from app.catalog.model import ProductStatus
from app.catalog.repository import ProductRepository
from app.orders.model import Order, OrderItem, OrderStatus
from app.orders.repository import OrderRepository
from app.orders.service import (
    DuplicateProductsError,
    EmptyOrderError,
    OrderService,
    ProductsUnavailableError,
)


@pytest.mark.asyncio
async def test_create_order_copies_product_data(db_session, order_data):
    buyer, _, products = order_data
    orders = OrderRepository(db_session)
    service = OrderService(
        order_repository=orders,
        product_repository=ProductRepository(db_session),
    )

    expected = {
        product.id: (product.title, product.price_amount) for product in products
    }

    order = await service.create(
        user_id=buyer.id,
        product_ids=[product.id for product in reversed(products)],
    )

    await db_session.commit()

    assert order.user_id == buyer.id
    assert order.status == OrderStatus.PENDING
    assert order.currency == "RUB"

    items = await orders.list_items_for_user(
        order_id=order.id,
        user_id=buyer.id,
    )

    assert len(items) == len(products)
    assert {
        item.product_id: (item.product_title, item.unit_price_amount) for item in items
    } == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("case", "expected_error"),
    [
        ("empty", EmptyOrderError),
        ("duplicate", DuplicateProductsError),
        ("missing", ProductsUnavailableError),
        ("draft", ProductsUnavailableError),
        ("archived", ProductsUnavailableError),
    ],
)
async def test_invalid_order_creates_no_records(
    db_session,
    order_data,
    case,
    expected_error,
):
    buyer, _, products = order_data
    service = OrderService(
        order_repository=OrderRepository(db_session),
        product_repository=ProductRepository(db_session),
    )

    product_ids = [product.id for product in products]

    if case == "empty":
        product_ids = []
    elif case == "duplicate":
        product_ids.append(products[0].id)
    elif case == "missing":
        product_ids.append(9223372036854775807)
    elif case == "draft":
        products[1].status = ProductStatus.DRAFT
    elif case == "archived":
        products[1].status = ProductStatus.ARCHIVED

    await db_session.flush()

    with pytest.raises(expected_error):
        await service.create(
            user_id=buyer.id,
            product_ids=product_ids,
        )

    order_ids = await db_session.scalars(select(Order.id))
    item_ids = await db_session.scalars(select(OrderItem.id))

    assert order_ids.all() == []
    assert item_ids.all() == []

    await db_session.rollback()
