from sqlalchemy import func, select
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from app.orders.model import Order, OrderItem


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        order: Order,
        items: list[OrderItem],
    ) -> Order:
        self._session.add(order)
        await self._session.flush()

        for item in items:
            item.order_id = order.id

        self._session.add_all(items)
        await self._session.flush()
        await self._session.refresh(order)

        return order

    async def get_by_id_for_user(
        self,
        *,
        order_id: int,
        user_id: int,
    ) -> Order | None:
        statement = select(Order).where(
            Order.id == order_id,
            Order.user_id == user_id,
        )

        result = await self._session.execute(statement)

        return result.scalar_one_or_none()

    async def list_items_for_user(
        self,
        *,
        order_id: int,
        user_id: int,
    ) -> list[OrderItem]:
        statement = (
            select(OrderItem)
            .join(Order, OrderItem.order_id == Order.id)
            .where(
                Order.id == order_id,
                Order.user_id == user_id,
            )
            .order_by(OrderItem.id)
        )

        result = await self._session.execute(statement)

        return list(result.scalars().all())

    async def list_for_user(
        self,
        *,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
    ) -> list[RowMapping]:
        statement = (
            select(
                Order.id,
                Order.status,
                Order.currency,
                Order.created_at,
                func.sum(OrderItem.unit_price_amount).label("total_amount"),
            )
            .join(OrderItem, OrderItem.order_id == Order.id)
            .where(Order.user_id == user_id)
            .group_by(Order.id)
            .order_by(Order.id.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self._session.execute(statement)

        return list(result.mappings().all())
