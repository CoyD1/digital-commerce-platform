from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog.model import Product, ProductStatus
from app.catalog.repository import ProductRepository
from app.catalog.schemas import ProductCreate, ProductRead
from app.catalog.service import (
    ProductCannotBePublishedError,
    ProductNotFoundError,
    ProductService,
)
from app.db.session import get_session
from app.users.dependencies import require_admin

router = APIRouter(
    prefix="/api/v1/products",
    tags=["catalog"],
)


@router.get("", response_model=list[ProductRead])
async def list_products(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    repository = ProductRepository(session)

    return await repository.list_published(
        limit=limit,
        offset=offset,
    )


@router.get("/{slug}", response_model=ProductRead)
async def get_product(
    slug: str,
    session: AsyncSession = Depends(get_session),
):
    repository = ProductRepository(session)

    product = await repository.get_published_by_slug(slug)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product


@router.post(
    "",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_product(
    data: ProductCreate,
    session: AsyncSession = Depends(get_session),
):
    repository = ProductRepository(session)

    product = Product(
        title=data.title,
        slug=data.slug,
        description=data.description,
        price_amount=data.price_amount,
        currency=data.currency,
        status=ProductStatus.DRAFT,
    )

    try:
        product = await repository.create(product)
        await session.commit()
    except IntegrityError as error:
        await session.rollback()

        diagnostics = getattr(error.orig, "diag", None)
        constraint_name = getattr(diagnostics, "constraint_name", None)

        if constraint_name == "products_slug_key":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Product slug already exists",
            ) from error

        raise

    return product


@router.post(
    "/{product_id}/publish",
    response_model=ProductRead,
    dependencies=[Depends(require_admin)],
)
async def publish_product(
    product_id: Annotated[int, Path(gt=0, le=9223372036854775807)],
    session: AsyncSession = Depends(get_session),
):
    repository = ProductRepository(session)
    service = ProductService(repository)

    try:
        product = await service.publish(product_id)
        await session.commit()

    except ProductNotFoundError:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        ) from None

    except ProductCannotBePublishedError:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only draft products can be published",
        ) from None

    return product
