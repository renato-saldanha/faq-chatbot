from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import select
from sqlalchemy.dialects import postgresql

from app.models import Interacao
from app.repositories._date_filter import apply_date_range
from app.repositories.faq_metrics_repository import FaqMetricsRepository
from app.repositories.interacao_repository import InteracaoRepository
from app.repositories.timeseries_metrics_repository import TimeseriesMetricsRepository

DIA = date(2026, 11, 27)
DIA_SEGUINTE = date(2026, 11, 28)


def _sql_e_params(query) -> tuple[str, list]:
    compiled = query.compile(dialect=postgresql.dialect())
    return str(compiled), list(compiled.params.values())


def _session_mock() -> MagicMock:
    session = MagicMock()
    result = MagicMock()
    result.one.return_value = (0, 0)
    result.all.return_value = []
    result.scalars.return_value.all.return_value = []
    session.execute = AsyncMock(return_value=result)
    return session


def test_date_to_inclui_o_proprio_dia_final():
    """Regressão: `criado_em <= date_to` comparava com a meia-noite e deixava o dia final de fora."""
    sql, params = _sql_e_params(apply_date_range(select(Interacao.id), DIA, DIA))

    assert "criado_em >=" in sql
    assert "criado_em <" in sql
    assert "criado_em <=" not in sql
    assert params == [DIA, DIA_SEGUINTE]


def test_sem_datas_nao_filtra():
    sql, params = _sql_e_params(apply_date_range(select(Interacao.id), None, None))

    assert "WHERE" not in sql
    assert params == []


def test_so_date_from():
    sql, params = _sql_e_params(apply_date_range(select(Interacao.id), DIA, None))

    assert "criado_em >=" in sql
    assert params == [DIA]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "consulta",
    [
        lambda s: TimeseriesMetricsRepository(s).get_summary(DIA, DIA),
        lambda s: TimeseriesMetricsRepository(s).get_daily_series(DIA, DIA),
        lambda s: FaqMetricsRepository(s).get_top_questions(DIA, DIA),
        lambda s: FaqMetricsRepository(s).get_category_breakdown(DIA, DIA),
        lambda s: InteracaoRepository(s).get_unanswered(DIA, DIA),
    ],
    ids=["summary", "daily_series", "top_questions", "category_breakdown", "unanswered"],
)
async def test_repositorios_incluem_o_dia_final(consulta):
    session = _session_mock()

    await consulta(session)

    sql, params = _sql_e_params(session.execute.call_args[0][0])
    assert "criado_em <=" not in sql
    assert DIA_SEGUINTE in params
