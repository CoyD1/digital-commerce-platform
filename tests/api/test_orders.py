from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.catalog.model import Product, ProductStatus
from app.core.security import create_access_token
from app.orders.model import Order, OrderItem
from app.users.model import User, UserRole, UserStatus


@pytest_asyncio.fixture
async def checkout_data(db_session):
    buyer = User(
        name="Buyer",
        email="checkout-buyer@example.com",
        password_hash="unused-in-this-test",
        status=UserStatus.ACTIVE,
    )

    products = [
        Product(
            title="Python Course",
            slug="checkout-python",
            description="Python course",
            price_amount=Decimal("1499.90"),
            status=ProductStatus.PUBLISHED,
        ),
        Product(
            title="SQL Course",
            slug="checkout-sql",
            description="SQL course",
            price_amount=Decimal("990.00"),
            status=ProductStatus.PUBLISHED,
        ),
    ]

    db_session.add_all([buyer, *products])
    await db_session.flush()

    headers = {
        "Authorization": f"Bearer {create_access_token(buyer.id)}",
    }

    return buyer, products, headers


@pytest_asyncio.fixture
async def placed_order(client, checkout_data):
    _, products, headers = checkout_data

    response = await client.post(
        "/api/v1/orders",
        json={"product_ids": [product.id for product in products]},
        headers=headers,
    )

    assert response.status_code == 201

    return response.json()


@pytest.mark.asyncio
async def test_create_order_returns_items_and_total(
    client,
    db_session,
    checkout_data,
):
    buyer, products, headers = checkout_data

    response = await client.post(
        "/api/v1/orders",
        json={"product_ids": [product.id for product in products]},
        headers=headers,
    )

    assert response.status_code == 201

    body = response.json()

    assert body["status"] == "PENDING"
    assert body["currency"] == "RUB"
    assert body["total_amount"] == "2489.90"
    assert len(body["items"]) == 2
    assert {
        item["product_id"]: (
            item["product_title"],
            item["unit_price_amount"],
        )
        for item in body["items"]
    } == {
        products[0].id: ("Python Course", "1499.90"),
        products[1].id: ("SQL Course", "990.00"),
    }

    order = await db_session.get(Order, body["id"])

    assert order is not None
    assert order.user_id == buyer.id


@pytest.mark.asyncio
async def test_create_order_requires_authentication(client):
    response = await client.post(
        "/api/v1/orders",
        json={"product_ids": [1]},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {"product_ids": []},
        {"product_ids": [1, 1]},
        {"product_ids": [0]},
        {"product_ids": [-1]},
        {"product_ids": ["1"]},
        {"product_ids": [True]},
        {"product_ids": [9223372036854775808]},
        {"product_ids": list(range(1, 102))},
        {"product_ids": [1], "user_id": 999},
        {"product_ids": [1], "price": "0.01"},
    ],
)
async def test_create_order_rejects_invalid_payload(
    client,
    db_session,
    checkout_data,
    payload,
):
    _, _, headers = checkout_data

    response = await client.post(
        "/api/v1/orders",
        json=payload,
        headers=headers,
    )

    assert response.status_code == 422
    assert await db_session.scalar(select(Order.id)) is None
    assert await db_session.scalar(select(OrderItem.id)) is None


@pytest.mark.asyncio
@pytest.mark.parametrize("case", ["missing", "draft", "archived"])
async def test_unavailable_product_rejects_entire_order(
    client,
    db_session,
    checkout_data,
    case,
):
    _, products, headers = checkout_data
    product_ids = [product.id for product in products]

    if case == "missing":
        product_ids.append(9223372036854775807)
    elif case == "draft":
        products[1].status = ProductStatus.DRAFT
    else:
        products[1].status = ProductStatus.ARCHIVED

    await db_session.flush()

    response = await client.post(
        "/api/v1/orders",
        json={"product_ids": product_ids},
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "One or more products are unavailable",
    }
    assert await db_session.scalar(select(Order.id)) is None
    assert await db_session.scalar(select(OrderItem.id)) is None


@pytest.mark.asyncio
async def test_get_order_keeps_purchase_data(
    client,
    db_session,
    checkout_data,
    placed_order,
):
    _, products, headers = checkout_data

    products[0].title = "New Course Title"
    products[0].price_amount = Decimal("9999.00")
    await db_session.commit()

    response = await client.get(
        f"/api/v1/orders/{placed_order['id']}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == placed_order

    list_response = await client.get(
        "/api/v1/orders",
        headers=headers,
    )

    assert list_response.status_code == 200
    assert list_response.json()[0]["total_amount"] == "2489.90"


@pytest.mark.asyncio
async def test_list_orders_returns_summaries_and_pagination(
    client,
    checkout_data,
):
    _, products, headers = checkout_data
    created = []

    for _ in range(3):
        response = await client.post(
            "/api/v1/orders",
            json={"product_ids": [product.id for product in products]},
            headers=headers,
        )

        assert response.status_code == 201
        created.append(response.json())

    response = await client.get(
        "/api/v1/orders",
        headers=headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert [order["id"] for order in body] == [
        order["id"] for order in reversed(created)
    ]
    assert all(order["total_amount"] == "2489.90" for order in body)
    assert all(order["status"] == "PENDING" for order in body)
    assert all(order["currency"] == "RUB" for order in body)
    assert all("created_at" in order for order in body)
    assert all("items" not in order for order in body)

    page = await client.get(
        "/api/v1/orders?limit=1&offset=1",
        headers=headers,
    )

    assert page.status_code == 200
    assert [order["id"] for order in page.json()] == [created[1]["id"]]

    empty_page = await client.get(
        "/api/v1/orders?offset=100",
        headers=headers,
    )

    assert empty_page.status_code == 200
    assert empty_page.json() == []


@pytest.mark.asyncio
@pytest.mark.parametrize("role", [UserRole.CUSTOMER, UserRole.ADMIN])
async def test_other_user_cannot_read_orders(
    client,
    db_session,
    placed_order,
    role,
):
    other_user = User(
        name="Other User",
        email="other-order-reader@example.com",
        password_hash="unused-in-this-test",
        status=UserStatus.ACTIVE,
        role=role,
    )

    db_session.add(other_user)
    await db_session.flush()

    headers = {
        "Authorization": f"Bearer {create_access_token(other_user.id)}",
    }

    detail_response = await client.get(
        f"/api/v1/orders/{placed_order['id']}",
        headers=headers,
    )

    assert detail_response.status_code == 404
    assert detail_response.json() == {"detail": "Order not found"}

    list_response = await client.get(
        "/api/v1/orders",
        headers=headers,
    )

    assert list_response.status_code == 200
    assert list_response.json() == []


@pytest.mark.asyncio
async def test_get_missing_order_returns_404(client, checkout_data):
    _, _, headers = checkout_data

    response = await client.get(
        "/api/v1/orders/9223372036854775807",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Order not found"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path",
    ["/api/v1/orders", "/api/v1/orders/1"],
)
async def test_read_orders_requires_authentication(client, path):
    response = await client.get(path)

    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/orders?limit=0",
        "/api/v1/orders?limit=101",
        "/api/v1/orders?offset=-1",
        "/api/v1/orders/0",
        "/api/v1/orders/9223372036854775808",
    ],
)
async def test_read_orders_rejects_invalid_parameters(
    client,
    checkout_data,
    path,
):
    _, _, headers = checkout_data

    response = await client.get(path, headers=headers)

    assert response.status_code == 422
