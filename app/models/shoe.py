from sqlalchemy import Boolean, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

from pgvector.sqlalchemy import Vector


class Shoe(Base):
    __tablename__ = "shoes"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    brand: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    model: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    embedding = mapped_column(
        Vector(768),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )    

    def build_embedding_text(self) -> str:
        return f"""
品牌：{self.brand}
型號：{self.model}
價格：NT$ {self.price}
產品描述：{self.description}
""".strip()    
   