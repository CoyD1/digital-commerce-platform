from app.catalog.model import ProductStatus
from app.catalog.repository import ProductRepository
from app.orders.model import Order, OrderItem, OrderStatus
from app.orders.repository import OrderRepository


class EmptyOrderError(Exception):
    pass


class DuplicateProductsError(Exception):
    pass


class ProductsUnavailableError(Exception):
    pass


class OrderNotFoundError(Exception):
    pass


class OrderCannotBeCancelledError(Exception):
    pass


class OrderService:
    def __init__(
        self,
        order_repository: OrderRepository,
        product_repository: ProductRepository,
    ) -> None:
        self._orders = order_repository
        self._products = product_repository

    async def create(
        self,
        *,
        user_id: int,
        product_ids: list[int],
    ) -> Order:
        if not product_ids:
            raise EmptyOrderError

        if len(product_ids) != len(set(product_ids)):
            raise DuplicateProductsError

        products = await self._products.get_many_for_update(product_ids)

        if len(products) != len(product_ids):
            raise ProductsUnavailableError

        if any(product.status != ProductStatus.PUBLISHED for product in products):
            raise ProductsUnavailableError

        order = Order(
            user_id=user_id,
            status=OrderStatus.PENDING,
            currency="RUB",
        )

        items = [
            OrderItem(
                product_id=product.id,
                product_title=product.title,
                unit_price_amount=product.price_amount,
            )
            for product in products
        ]

        return await self._orders.create(order, items)

    async def cancel(
        self,
        *,
        order_id: int,
        user_id: int,
    ) -> Order:
        order = await self._orders.get_by_id_for_user_for_update(
            order_id=order_id,
            user_id=user_id,
        )

        if order is None:
            raise OrderNotFoundError

        if order.status == OrderStatus.CANCELLED:
            return order

        if order.status != OrderStatus.PENDING:
            raise OrderCannotBeCancelledError

        order.status = OrderStatus.CANCELLED

        return order
