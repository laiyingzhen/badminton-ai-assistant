from decimal import Decimal

from sqlalchemy import Boolean, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Racket(Base):
    __tablename__ = "rackets"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    brand: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    model: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    weight: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    balance: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    flexibility: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    suitable_level: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    playing_style: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )