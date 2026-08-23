from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class FaqItem(Base):
    __tablename__ = "faq_item"

    id: Mapped[int] = mapped_column(primary_key=True)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categoria.id"), nullable=False)
    pergunta: Mapped[str] = mapped_column(Text, nullable=False)
    resposta: Mapped[str] = mapped_column(Text, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    categoria: Mapped["Categoria"] = relationship(back_populates="faq_items")  # noqa: F821
