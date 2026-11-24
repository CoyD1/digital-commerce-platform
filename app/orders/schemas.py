from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.orders.model import OrderStatus

ProductId = Annotated[
    int,
    Field(strict=True, gt=0, le=9223372036854775807),
]


class OrderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_ids: list[ProductId] = Field(
        min_length=1,
        max_length=100,
    )

    @field_validator("product_ids")
    @classmethod
    def reject_duplicates(cls, value: list[int]) -> list[int]:
        if len(value) != len(set(value)):
            raise ValueError("Product IDs must be unique")

        return value


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    product_title: str
    unit_price_amount: Decimal


class OrderRead(BaseModel):
    id: int
    status: OrderStatus
    currency: str
    total_amount: Decimal
    items: list[OrderItemRead]


class OrderSummary(BaseModel):
    id: int
    status: OrderStatus
    currency: str
    total_amount: Decimal
    created_at: datetime
