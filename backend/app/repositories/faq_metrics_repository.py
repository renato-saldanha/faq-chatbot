from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Categoria, FaqItem, Interacao
from app.repositories._date_filter import apply_date_range


@dataclass(frozen=True)
class TopQuestion:
    faq_item_id: int
    pergunta: str
    quantidade: int


@dataclass(frozen=True)
class CategoryBreakdown:
    categoria: str
    quantidade: int


class FaqMetricsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_top_questions(
        self, date_from: date | None, date_to: date | None, limit: int = 10
    ) -> list[TopQuestion]:
        quantidade = func.count(Interacao.id).label("quantidade")
        query = (
            select(FaqItem.id, FaqItem.pergunta, quantidade)
            .join(FaqItem, FaqItem.id == Interacao.faq_item_id)
            .where(Interacao.faq_item_id.is_not(None))
            .group_by(FaqItem.id, FaqItem.pergunta)
            .order_by(quantidade.desc())
            .limit(limit)
        )
        query = apply_date_range(query, date_from, date_to)
        result = await self._session.execute(query)
        return [TopQuestion(faq_item_id=row[0], pergunta=row[1], quantidade=row[2]) for row in result.all()]

    async def get_category_breakdown(self, date_from: date | None, date_to: date | None) -> list[CategoryBreakdown]:
        quantidade = func.count(Interacao.id).label("quantidade")
        query = (
            select(Categoria.nome, quantidade)
            .join(Categoria, Categoria.id == Interacao.categoria_id)
            .where(Interacao.categoria_id.is_not(None))
            .group_by(Categoria.nome)
            .order_by(quantidade.desc())
        )
        query = apply_date_range(query, date_from, date_to)
        result = await self._session.execute(query)
        return [CategoryBreakdown(categoria=row[0], quantidade=row[1]) for row in result.all()]
