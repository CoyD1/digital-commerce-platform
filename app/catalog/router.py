from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog.repository import ProductRepository
from app.catalog.schemas import ProductRead
from app.db.session import get_session

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
