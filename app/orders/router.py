from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog.repository import ProductRepository
from app.db.session import get_session
from app.orders.repository import OrderRepository
from app.orders.schemas import OrderCreate, OrderItemRead, OrderRead
from app.orders.service import (
    DuplicateProductsError,
    EmptyOrderError,
    OrderService,
    ProductsUnavailableError,
)
from app.users.dependencies import get_current_user
from app.users.model import User

router = APIRouter(
    prefix="/api/v1/orders",
    tags=["orders"],
)


@router.post(
    "",
    response_model=OrderRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_order(
    data: OrderCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> OrderRead:
    orders = OrderRepository(session)
    service = OrderService(
        order_repository=orders,
        product_repository=ProductRepository(session),
    )

    try:
        order = await service.create(
            user_id=current_user.id,
            product_ids=data.product_ids,
        )

        items = await orders.list_items_for_user(
            order_id=order.id,
            user_id=current_user.id,
        )

        response = OrderRead(
            id=order.id,
            status=order.status,
            currency=order.currency,
            total_amount=sum(
                (item.unit_price_amount for item in items),
                Decimal("0.00"),
            ),
            items=[
                OrderItemRead.model_validate(item)
                for item in items
            ],
        )

        await session.commit()

    except (EmptyOrderError, DuplicateProductsError):
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Order must contain unique product IDs",
        ) from None

    except ProductsUnavailableError:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="One or more products are unavailable",
        ) from None

    except Exception:
        await session.rollback()
        raise

    return response