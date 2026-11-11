from app.catalog.model import Product, ProductStatus
from app.catalog.repository import ProductRepository


class ProductNotFoundError(Exception):
    pass


class ProductCannotBePublishedError(Exception):
    pass


class ProductService:
    def __init__(self, repository: ProductRepository) -> None:
        self._repository = repository

    async def publish(self, product_id: int) -> Product:
        product = await self._repository.get_by_id_for_update(product_id)

        if product is None:
            raise ProductNotFoundError

        if product.status != ProductStatus.DRAFT:
            raise ProductCannotBePublishedError

        product.status = ProductStatus.PUBLISHED

        return product
