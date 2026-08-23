from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Interacao


@dataclass(frozen=True)
class MetricsSummary:
    total_conversas: int
    total_sem_resposta: int
    taxa_sem_resposta: float


@dataclass(frozen=True)
class DailyCount:
    data: str
    quantidade: int


class TimeseriesMetricsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _apply_date_filter(self, query, date_from: date | None, date_to: date | None):
        if date_from is not None:
            query = query.where(Interacao.criado_em >= date_from)
        if date_to is not None:
            query = query.where(Interacao.criado_em <= date_to)
        return query

    async def get_summary(self, date_from: date | None, date_to: date | None) -> MetricsSummary:
        query = select(
            func.count(Interacao.id),
            func.count(Interacao.id).filter(Interacao.sem_resposta.is_(True)),
        )
        query = self._apply_date_filter(query, date_from, date_to)
        result = await self._session.execute(query)
        total, total_sem_resposta = result.one()

        taxa = (total_sem_resposta / total) if total else 0.0
        return MetricsSummary(
            total_conversas=total,
            total_sem_resposta=total_sem_resposta,
            taxa_sem_resposta=round(taxa, 4),
        )

    async def get_daily_series(self, date_from: date | None, date_to: date | None) -> list[DailyCount]:
        dia = func.date(Interacao.criado_em).label("dia")
        query = select(dia, func.count(Interacao.id)).group_by(dia).order_by(dia)
        query = self._apply_date_filter(query, date_from, date_to)
        result = await self._session.execute(query)
        return [DailyCount(data=str(row[0]), quantidade=row[1]) for row in result.all()]
