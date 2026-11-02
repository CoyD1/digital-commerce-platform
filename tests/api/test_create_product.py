import pytest
import pytest_asyncio

from app.catalog.model import ProductStatus
from app.catalog.repository import ProductRepository
from app.core.security import create_access_token
from app.users.model import User, UserRole, UserStatus
from app.users.repository import UserRepository


@pytest.fixture
def product_payload():
    return {
        "title": "Python Course",
        "slug": "python-course",
        "description": "Practical Python course",
        "price_amount": "1499.90",
        "currency": "RUB",
    }


@pytest_asyncio.fixture
async def admin_headers(db_session):
    repository = UserRepository(db_session)

    user = await repository.create(
        User(
            name="Admin",
            email="catalog-admin@example.com",
            password_hash="unused-in-this-test",
            status=UserStatus.ACTIVE,
            role=UserRole.ADMIN,
        )
    )

    token = create_access_token(user.id)

    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_admin_creates_draft_product(
    client,
    db_session,
    admin_headers,
    product_payload,
):
    response = await client.post(
        "/api/v1/products",
        json=product_payload,
        headers=admin_headers,
    )

    assert response.status_code == 201

    body = response.json()
    assert body["slug"] == product_payload["slug"]
    assert body["price_amount"] == "1499.90"
    assert body["currency"] == "RUB"
    assert body["status"] == "DRAFT"

    repository = ProductRepository(db_session)
    product = await repository.get_by_slug(product_payload["slug"])

    assert product is not None
    assert product.id == body["id"]
    assert product.status == ProductStatus.DRAFT

    public_response = await client.get(f"/api/v1/products/{product_payload['slug']}")

    assert public_response.status_code == 404


@pytest.mark.asyncio
async def test_create_product_requires_authentication(
    client,
    product_payload,
):
    response = await client.post(
        "/api/v1/products",
        json=product_payload,
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_customer_cannot_create_product(
    client,
    db_session,
    product_payload,
):
    repository = UserRepository(db_session)

    user = await repository.create(
        User(
            name="Customer",
            email="catalog-customer@example.com",
            password_hash="unused-in-this-test",
            status=UserStatus.ACTIVE,
            role=UserRole.CUSTOMER,
        )
    )

    token = create_access_token(user.id)

    response = await client.post(
        "/api/v1/products",
        json=product_payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403

    products = ProductRepository(db_session)
    assert await products.get_by_slug(product_payload["slug"]) is None


@pytest.mark.asyncio
async def test_create_product_rejects_duplicate_slug(
    client,
    admin_headers,
    product_payload,
):
    first_response = await client.post(
        "/api/v1/products",
        json=product_payload,
        headers=admin_headers,
    )

    assert first_response.status_code == 201

    second_response = await client.post(
        "/api/v1/products",
        json=product_payload,
        headers=admin_headers,
    )

    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "Product slug already exists",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("title", "   "),
        ("slug", "Invalid slug"),
        ("price_amount", "0"),
        ("price_amount", "12.345"),
        ("currency", "USD"),
        ("status", "PUBLISHED"),
    ],
)
async def test_create_product_rejects_invalid_fields(
    client,
    admin_headers,
    product_payload,
    field,
    value,
):
    product_payload[field] = value

    response = await client.post(
        "/api/v1/products",
        json=product_payload,
        headers=admin_headers,
    )

    assert response.status_code == 422
