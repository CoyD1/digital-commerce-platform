from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.catalog.model import Product, ProductStatus
from app.catalog.repository import ProductRepository


@pytest.mark.asyncio
async def test_create_product_sets_defaults(db_session):
    repository = ProductRepository(db_session)

    product = Product(
        title="Python Course",
        slug="python-course",
        description="Backend development course",
        price_amount=Decimal("1499.90"),
    )

    created_product = await repository.create(product)

    assert created_product.id is not None
    assert created_product.title == "Python Course"
    assert created_product.slug == "python-course"
    assert created_product.price_amount == Decimal("1499.90")
    assert created_product.currency == "RUB"
    assert created_product.status == ProductStatus.DRAFT
    assert created_product.created_at is not None
    assert created_product.updated_at is not None

    stored_product = await repository.get_by_id(created_product.id)

    assert stored_product is not None
    assert stored_product.slug == "python-course"
    assert stored_product.price_amount == Decimal("1499.90")


@pytest.mark.asyncio
async def test_get_by_slug_returns_product(db_session):
    repository = ProductRepository(db_session)

    created_product = await repository.create(
        Product(
            title="SQL Course",
            slug="sql-course",
            description="PostgreSQL fundamentals",
            price_amount=Decimal("990.00"),
        )
    )

    result = await repository.get_by_slug("sql-course")

    assert result is not None
    assert result.id == created_product.id
    assert result.slug == "sql-course"


@pytest.mark.asyncio
async def test_get_by_slug_returns_none_for_unknown_slug(db_session):
    repository = ProductRepository(db_session)

    result = await repository.get_by_slug("missing-product")

    assert result is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "price",
    [Decimal("0.00"), Decimal("-10.00")],
)
async def test_create_rejects_non_positive_price(db_session, price):
    repository = ProductRepository(db_session)

    product = Product(
        title="Invalid Price",
        slug="invalid-price",
        description="Product with an invalid price",
        price_amount=price,
    )

    with pytest.raises(IntegrityError) as error:
        await repository.create(product)

    assert error.value.orig.diag.constraint_name == "ck_products_price_positive"

    await db_session.rollback()


@pytest.mark.asyncio
async def test_create_rejects_duplicate_slug(db_session):
    repository = ProductRepository(db_session)

    await repository.create(
        Product(
            title="First Product",
            slug="duplicate-slug",
            description="First product",
            price_amount=Decimal("100.00"),
        )
    )

    duplicate = Product(
        title="Second Product",
        slug="duplicate-slug",
        description="Second product",
        price_amount=Decimal("200.00"),
    )

    with pytest.raises(IntegrityError) as error:
        await repository.create(duplicate)

    assert error.value.orig.diag.constraint_name == "products_slug_key"

    await db_session.rollback()


@pytest.mark.asyncio
async def test_create_rejects_unsupported_currency(db_session):
    repository = ProductRepository(db_session)

    product = Product(
        title="Unsupported Currency",
        slug="unsupported-currency",
        description="Product priced in USD",
        price_amount=Decimal("100.00"),
        currency="USD",
    )

    with pytest.raises(IntegrityError) as error:
        await repository.create(product)

    assert error.value.orig.diag.constraint_name == "ck_products_currency_rub"

    await db_session.rollback()


@pytest.mark.asyncio
async def test_list_published_excludes_drafts_and_archived(db_session):
    repository = ProductRepository(db_session)

    published = None

    for product_status in ProductStatus:
        product = await repository.create(
            Product(
                title=f"{product_status.value} Product",
                slug=f"product-{product_status.value.lower()}",
                description="Catalog visibility test",
                price_amount=Decimal("100.00"),
                status=product_status,
            )
        )

        if product_status == ProductStatus.PUBLISHED:
            published = product

    assert published is not None

    products = await repository.list_published()

    assert [product.id for product in products] == [published.id]


@pytest.mark.asyncio
async def test_list_published_applies_order_limit_and_offset(db_session):
    repository = ProductRepository(db_session)

    created_products = []

    for number in range(3):
        product = await repository.create(
            Product(
                title=f"Product {number}",
                slug=f"pagination-product-{number}",
                description="Pagination test",
                price_amount=Decimal("100.00"),
                status=ProductStatus.PUBLISHED,
            )
        )
        created_products.append(product)

    products = await repository.list_published(
        limit=1,
        offset=1,
    )

    assert [product.id for product in products] == [created_products[1].id]


@pytest.mark.asyncio
async def test_list_published_returns_empty_list_beyond_last_page(
    db_session,
):
    repository = ProductRepository(db_session)

    await repository.create(
        Product(
            title="Only Product",
            slug="only-product",
            description="Single published product",
            price_amount=Decimal("100.00"),
            status=ProductStatus.PUBLISHED,
        )
    )

    products = await repository.list_published(
        limit=20,
        offset=100,
    )

    assert products == []
