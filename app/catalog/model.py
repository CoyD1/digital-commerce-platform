from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Identity,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProductStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Product(Base):
    __tablename__ = "products"

    __table_args__ = (
        CheckConstraint(
            "price_amount > 0",
            name="ck_products_price_positive",
        ),
        CheckConstraint(
            "currency = 'RUB'",
            name="ck_products_currency_rub",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)

    slug: Mapped[str] = mapped_column(
        String(200),
        unique=True,
        nullable=False,
    )

    description: Mapped[str] = mapped_column(Text, nullable=False)

    price_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        server_default="RUB",
        nullable=False,
    )

    status: Mapped[ProductStatus] = mapped_column(
        SQLEnum(ProductStatus, name="product_status"),
        server_default=ProductStatus.DRAFT.value,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
