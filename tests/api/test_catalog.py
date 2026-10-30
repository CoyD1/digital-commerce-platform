from decimal import Decimal

import pytest

from app.catalog.model import Product, ProductStatus
from app.catalog.repository import ProductRepository


@pytest.mark.asyncio
async def test_list_products_returns_only_published_products(
    client,
    db_session,
):
    repository = ProductRepository(db_session)

    published = await repository.create(
        Product(
            title="Published Product",
            slug="published-product",
            description="Visible product",
            price_amount=Decimal("100.00"),
            status=ProductStatus.PUBLISHED,
        )
    )

    await repository.create(
        Product(
            title="Draft Product",
            slug="draft-product",
            description="Hidden product",
            price_amount=Decimal("200.00"),
            status=ProductStatus.DRAFT,
        )
    )

    await repository.create(
        Product(
            title="Archived Product",
            slug="archived-product",
            description="Archived product",
            price_amount=Decimal("300.00"),
            status=ProductStatus.ARCHIVED,
        )
    )

    response = await client.get("/api/v1/products")

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1
    assert body[0]["id"] == published.id
    assert body[0]["slug"] == "published-product"
    assert body[0]["price_amount"] == "100.00"
    assert body[0]["currency"] == "RUB"
    assert body[0]["status"] == "PUBLISHED"


@pytest.mark.asyncio
async def test_list_products_applies_pagination(
    client,
    db_session,
):
    repository = ProductRepository(db_session)

    created_products = []

    for number in range(3):
        product = await repository.create(
            Product(
                title=f"Product {number}",
                slug=f"api-product-{number}",
                description="Pagination product",
                price_amount=Decimal("100.00"),
                status=ProductStatus.PUBLISHED,
            )
        )
        created_products.append(product)

    response = await client.get("/api/v1/products?limit=1&offset=1")

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1
    assert body[0]["id"] == created_products[1].id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query",
    [
        "?limit=0",
        "?limit=101",
        "?offset=-1",
    ],
)
async def test_list_products_rejects_invalid_pagination(
    client,
    query,
):
    response = await client.get(f"/api/v1/products{query}")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_product_returns_published_product(
    client,
    db_session,
):
    repository = ProductRepository(db_session)

    product = await repository.create(
        Product(
            title="Backend Course",
            slug="backend-course",
            description="Course description",
            price_amount=Decimal("1499.90"),
            status=ProductStatus.PUBLISHED,
        )
    )

    response = await client.get("/api/v1/products/backend-course")

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == product.id
    assert body["slug"] == "backend-course"
    assert body["title"] == "Backend Course"
    assert body["price_amount"] == "1499.90"


@pytest.mark.asyncio
async def test_get_product_does_not_return_draft(
    client,
    db_session,
):
    repository = ProductRepository(db_session)

    await repository.create(
        Product(
            title="Draft Course",
            slug="draft-course",
            description="Hidden course",
            price_amount=Decimal("100.00"),
            status=ProductStatus.DRAFT,
        )
    )

    response = await client.get("/api/v1/products/draft-course")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Product not found",
    }


@pytest.mark.asyncio
async def test_get_product_returns_404_for_unknown_slug(client):
    response = await client.get("/api/v1/products/missing-course")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Product not found",
    }
