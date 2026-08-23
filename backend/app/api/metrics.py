from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api._deps import require_admin_session
from app.db import get_db_session
from app.repositories.faq_metrics_repository import FaqMetricsRepository
from app.repositories.interacao_repository import InteracaoRepository
from app.repositories.timeseries_metrics_repository import TimeseriesMetricsRepository

router = APIRouter(prefix="/api/metrics", tags=["metrics"], dependencies=[Depends(require_admin_session)])


class MetricsSummaryOut(BaseModel):
    total_conversas: int
    total_sem_resposta: int
    taxa_sem_resposta: float


class DailyCountOut(BaseModel):
    data: str
    quantidade: int


class TopQuestionOut(BaseModel):
    faq_item_id: int
    pergunta: str
    quantidade: int


class CategoryBreakdownOut(BaseModel):
    categoria: str
    quantidade: int


class UnansweredQuestionOut(BaseModel):
    id: int
    pergunta_usuario: str
    criado_em: str


def get_timeseries_metrics_repository(
    session: AsyncSession = Depends(get_db_session),
) -> TimeseriesMetricsRepository:
    return TimeseriesMetricsRepository(session)


def get_faq_metrics_repository(session: AsyncSession = Depends(get_db_session)) -> FaqMetricsRepository:
    return FaqMetricsRepository(session)


def get_interacao_repository(session: AsyncSession = Depends(get_db_session)) -> InteracaoRepository:
    return InteracaoRepository(session)


@router.get("/summary", response_model=MetricsSummaryOut)
async def get_summary(
    date_from: date | None = None,
    date_to: date | None = None,
    repo: TimeseriesMetricsRepository = Depends(get_timeseries_metrics_repository),
) -> MetricsSummaryOut:
    summary = await repo.get_summary(date_from, date_to)
    return MetricsSummaryOut(
        total_conversas=summary.total_conversas,
        total_sem_resposta=summary.total_sem_resposta,
        taxa_sem_resposta=summary.taxa_sem_resposta,
    )


@router.get("/timeseries", response_model=list[DailyCountOut])
async def get_timeseries(
    date_from: date | None = None,
    date_to: date | None = None,
    repo: TimeseriesMetricsRepository = Depends(get_timeseries_metrics_repository),
) -> list[DailyCountOut]:
    series = await repo.get_daily_series(date_from, date_to)
    return [DailyCountOut(data=d.data, quantidade=d.quantidade) for d in series]


@router.get("/top-questions", response_model=list[TopQuestionOut])
async def get_top_questions(
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 10,
    repo: FaqMetricsRepository = Depends(get_faq_metrics_repository),
) -> list[TopQuestionOut]:
    top = await repo.get_top_questions(date_from, date_to, limit)
    return [TopQuestionOut(faq_item_id=t.faq_item_id, pergunta=t.pergunta, quantidade=t.quantidade) for t in top]


@router.get("/categories", response_model=list[CategoryBreakdownOut])
async def get_categories(
    date_from: date | None = None,
    date_to: date | None = None,
    repo: FaqMetricsRepository = Depends(get_faq_metrics_repository),
) -> list[CategoryBreakdownOut]:
    breakdown = await repo.get_category_breakdown(date_from, date_to)
    return [CategoryBreakdownOut(categoria=c.categoria, quantidade=c.quantidade) for c in breakdown]


@router.get("/unanswered", response_model=list[UnansweredQuestionOut])
async def get_unanswered(
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 50,
    repo: InteracaoRepository = Depends(get_interacao_repository),
) -> list[UnansweredQuestionOut]:
    interacoes = await repo.get_unanswered(date_from, date_to, limit)
    return [
        UnansweredQuestionOut(
            id=i.id,
            pergunta_usuario=i.pergunta_usuario,
            criado_em=i.criado_em.isoformat(),
        )
        for i in interacoes
    ]
