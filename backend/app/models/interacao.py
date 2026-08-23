from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Interacao(Base):
    __tablename__ = "interacao"

    id: Mapped[int] = mapped_column(primary_key=True)
    pergunta_usuario: Mapped[str] = mapped_column(Text, nullable=False)
    faq_item_id: Mapped[int | None] = mapped_column(ForeignKey("faq_item.id", ondelete="SET NULL"), nullable=True)
    categoria_id: Mapped[int | None] = mapped_column(ForeignKey("categoria.id", ondelete="SET NULL"), nullable=True)
    score_similaridade: Mapped[float | None] = mapped_column(Float, nullable=True)
    sem_resposta: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
