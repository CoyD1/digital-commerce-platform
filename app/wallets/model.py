from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Numeric,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WalletEntryType(str, Enum):
    TOP_UP = "TOP_UP"
    ORDER_PAYMENT = "ORDER_PAYMENT"


class Wallet(Base):
    __tablename__ = "wallets"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            name="uq_wallets_user_id",
        ),
        CheckConstraint(
            "balance_amount >= 0",
            name="ck_wallets_balance_non_negative",
        ),
        CheckConstraint(
            "currency = 'RUB'",
            name="ck_wallets_currency_rub",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    balance_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        server_default=text("0"),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        server_default="RUB",
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


class WalletEntry(Base):
    __tablename__ = "wallet_entries"

    __table_args__ = (
        UniqueConstraint(
            "operation_key",
            name="uq_wallet_entries_operation_key",
        ),
        UniqueConstraint(
            "order_id",
            name="uq_wallet_entries_order_id",
        ),
        CheckConstraint(
            """
            (
                entry_type = 'TOP_UP'
                AND amount > 0
                AND order_id IS NULL
            )
            OR
            (
                entry_type = 'ORDER_PAYMENT'
                AND amount < 0
                AND order_id IS NOT NULL
            )
            """,
            name="ck_wallet_entries_operation",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
    )

    wallet_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("wallets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    entry_type: Mapped[WalletEntryType] = mapped_column(
        SQLEnum(WalletEntryType, name="wallet_entry_type"),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    operation_key: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    order_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("orders.id", ondelete="RESTRICT"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
