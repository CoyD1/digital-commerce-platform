from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.catalog.model import Product
from app.orders.model import Order, OrderItem, OrderStatus
from app.orders.repository import OrderRepository


def make_order_item(product: Product) -> OrderItem:
    return OrderItem(
        product_id=product.id,
        product_title=product.title,
        unit_price_amount=product.price_amount,
    )


@pytest.mark.asyncio
async def test_create_order_with_two_items(db_session, order_data):
    buyer, _, products = order_data
    repository = OrderRepository(db_session)

    order = await repository.create(
        Order(user_id=buyer.id),
        [make_order_item(product) for product in products],
    )

    assert order.id is not None
    assert order.status == OrderStatus.PENDING
    assert order.currency == "RUB"
    assert order.created_at is not None
    assert order.updated_at is not None

    stored_order = await repository.get_by_id_for_user(
        order_id=order.id,
        user_id=buyer.id,
    )

    assert stored_order is not None
    assert stored_order.id == order.id

    items = await repository.list_items_for_user(
        order_id=order.id,
        user_id=buyer.id,
    )

    assert len(items) == 2
    assert {item.product_id for item in items} == {product.id for product in products}
    assert all(item.order_id == order.id for item in items)
    assert sum(
        (item.unit_price_amount for item in items),
        Decimal("0.00"),
    ) == Decimal("2489.90")


@pytest.mark.asyncio
async def test_another_user_cannot_read_order(db_session, order_data):
    buyer, another_buyer, products = order_data
    repository = OrderRepository(db_session)

    order = await repository.create(
        Order(user_id=buyer.id),
        [make_order_item(products[0])],
    )

    result = await repository.get_by_id_for_user(
        order_id=order.id,
        user_id=another_buyer.id,
    )

    items = await repository.list_items_for_user(
        order_id=order.id,
        user_id=another_buyer.id,
    )

    assert result is None
    assert items == []


@pytest.mark.asyncio
async def test_order_keeps_original_title_and_price(db_session, order_data):
    buyer, _, products = order_data
    product = products[0]
    repository = OrderRepository(db_session)

    order = await repository.create(
        Order(user_id=buyer.id),
        [make_order_item(product)],
    )

    product.title = "Updated Python Course"
    product.price_amount = Decimal("1999.90")
    await db_session.flush()

    items = await repository.list_items_for_user(
        order_id=order.id,
        user_id=buyer.id,
    )

    assert len(items) == 1

    await db_session.refresh(items[0])

    assert items[0].product_title == "Python Course"
    assert items[0].unit_price_amount == Decimal("1499.90")


@pytest.mark.asyncio
async def test_order_rejects_duplicate_product(db_session, order_data):
    buyer, _, products = order_data
    repository = OrderRepository(db_session)
    product = products[0]

    with pytest.raises(IntegrityError) as error:
        await repository.create(
            Order(user_id=buyer.id),
            [
                make_order_item(product),
                make_order_item(product),
            ],
        )

    assert error.value.orig.diag.constraint_name == "uq_order_items_order_product"

    await db_session.rollback()
