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


@pytest_asyncio.fixture
async def draft_product_id(client, admin_headers, product_payload):
    response = await client.post(
        "/api/v1/products",
        json=product_payload,
        headers=admin_headers,
    )

    assert response.status_code == 201

    return response.json()["id"]


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


@pytest.mark.asyncio
async def test_publish_makes_product_public(
    client,
    admin_headers,
    draft_product_id,
    product_payload,
):
    response = await client.post(
        f"/api/v1/products/{draft_product_id}/publish",
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "PUBLISHED"

    public_response = await client.get(f"/api/v1/products/{product_payload['slug']}")

    assert public_response.status_code == 200
    assert public_response.json()["id"] == draft_product_id

    list_response = await client.get("/api/v1/products")

    assert list_response.status_code == 200
    assert draft_product_id in [product["id"] for product in list_response.json()]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "existing_status",
    [ProductStatus.PUBLISHED, ProductStatus.ARCHIVED],
)
async def test_publish_rejects_non_draft_product(
    client,
    db_session,
    admin_headers,
    draft_product_id,
    existing_status,
):
    repository = ProductRepository(db_session)
    product = await repository.get_by_id(draft_product_id)

    assert product is not None

    product.status = existing_status
    await db_session.commit()

    response = await client.post(
        f"/api/v1/products/{draft_product_id}/publish",
        headers=admin_headers,
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Only draft products can be published",
    }

    saved_product = await repository.get_by_id(draft_product_id)

    assert saved_product is not None
    assert saved_product.status == existing_status


@pytest.mark.asyncio
async def test_publish_returns_404_for_missing_product(
    client,
    admin_headers,
):
    response = await client.post(
        "/api/v1/products/9223372036854775807/publish",
        headers=admin_headers,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Product not found"}


@pytest.mark.asyncio
async def test_publish_requires_authentication(
    client,
    draft_product_id,
):
    response = await client.post(
        f"/api/v1/products/{draft_product_id}/publish",
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_customer_cannot_publish_product(
    client,
    db_session,
    draft_product_id,
):
    users = UserRepository(db_session)

    customer = await users.create(
        User(
            name="Customer",
            email="publish-customer@example.com",
            password_hash="unused-in-this-test",
            status=UserStatus.ACTIVE,
            role=UserRole.CUSTOMER,
        )
    )

    token = create_access_token(customer.id)

    response = await client.post(
        f"/api/v1/products/{draft_product_id}/publish",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403

    products = ProductRepository(db_session)
    product = await products.get_by_id(draft_product_id)

    assert product is not None
    assert product.status == ProductStatus.DRAFT


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "initial_status",
    [ProductStatus.DRAFT, ProductStatus.PUBLISHED],
)
async def test_admin_archives_product(
    client,
    db_session,
    admin_headers,
    draft_product_id,
    product_payload,
    initial_status,
):
    repository = ProductRepository(db_session)
    product = await repository.get_by_id(draft_product_id)

    assert product is not None

    product.status = initial_status
    await db_session.commit()

    response = await client.post(
        f"/api/v1/products/{draft_product_id}/archive",
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ARCHIVED"

    await db_session.refresh(product)

    assert product.status == ProductStatus.ARCHIVED

    public_response = await client.get(f"/api/v1/products/{product_payload['slug']}")

    assert public_response.status_code == 404

    list_response = await client.get("/api/v1/products")

    assert list_response.status_code == 200
    assert draft_product_id not in [item["id"] for item in list_response.json()]


@pytest.mark.asyncio
async def test_archive_rejects_already_archived_product(
    client,
    admin_headers,
    draft_product_id,
):
    url = f"/api/v1/products/{draft_product_id}/archive"

    first_response = await client.post(url, headers=admin_headers)

    assert first_response.status_code == 200

    second_response = await client.post(url, headers=admin_headers)

    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "Only draft or published products can be archived",
    }


@pytest.mark.asyncio
async def test_archive_returns_404_for_missing_product(
    client,
    admin_headers,
):
    response = await client.post(
        "/api/v1/products/9223372036854775807/archive",
        headers=admin_headers,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Product not found"}


@pytest.mark.asyncio
async def test_archive_requires_authentication(
    client,
    draft_product_id,
):
    response = await client.post(
        f"/api/v1/products/{draft_product_id}/archive",
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_customer_cannot_archive_product(
    client,
    db_session,
    draft_product_id,
):
    users = UserRepository(db_session)

    customer = await users.create(
        User(
            name="Customer",
            email="archive-customer@example.com",
            password_hash="unused-in-this-test",
            status=UserStatus.ACTIVE,
            role=UserRole.CUSTOMER,
        )
    )

    token = create_access_token(customer.id)

    response = await client.post(
        f"/api/v1/products/{draft_product_id}/archive",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403

    products = ProductRepository(db_session)
    product = await products.get_by_id(draft_product_id)

    assert product is not None
    assert product.status == ProductStatus.DRAFT
