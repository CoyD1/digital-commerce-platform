from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog.model import Product, ProductStatus


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, product: Product) -> Product:
        self._session.add(product)

        await self._session.flush()
        await self._session.refresh(product)

        return product

    async def get_by_id(self, product_id: int) -> Product | None:
        statement = select(Product).where(Product.id == product_id)

        result = await self._session.execute(statement)

        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Product | None:
        statement = select(Product).where(Product.slug == slug)

        result = await self._session.execute(statement)

        return result.scalar_one_or_none()

    async def list_published(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Product]:
        statement = (
            select(Product)
            .where(Product.status == ProductStatus.PUBLISHED)
            .order_by(Product.id)
            .limit(limit)
            .offset(offset)
        )

        result = await self._session.execute(statement)

        return list(result.scalars().all())
