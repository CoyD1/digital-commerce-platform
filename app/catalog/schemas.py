from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.catalog.model import ProductStatus


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    description: str
    price_amount: Decimal
    currency: str
    status: ProductStatus


class ProductListQuery(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
