from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.repositories.timeseries_metrics_repository import DailyCount, TimeseriesMetricsRepository


def _mock_session_with_result(rows):
    session = MagicMock()
    result = MagicMock()
    result.one = MagicMock(return_value=rows if isinstance(rows, tuple) else rows)
    result.all = MagicMock(return_value=rows if isinstance(rows, list) else [])
    session.execute = AsyncMock(return_value=result)
    return session


@pytest.mark.asyncio
async def test_get_summary_calcula_taxa_sem_resposta():
    session = _mock_session_with_result((10, 3))
    repo = TimeseriesMetricsRepository(session)

    summary = await repo.get_summary(None, None)

    assert summary.total_conversas == 10
    assert summary.total_sem_resposta == 3
    assert summary.taxa_sem_resposta == 0.3


@pytest.mark.asyncio
async def test_get_summary_com_total_zero_nao_divide_por_zero():
    session = _mock_session_with_result((0, 0))
    repo = TimeseriesMetricsRepository(session)

    summary = await repo.get_summary(None, None)

    assert summary.total_conversas == 0
    assert summary.taxa_sem_resposta == 0.0


@pytest.mark.asyncio
async def test_get_summary_aplica_filtro_de_data():
    session = _mock_session_with_result((5, 1))
    repo = TimeseriesMetricsRepository(session)

    await repo.get_summary(date(2026, 1, 1), date(2026, 1, 31))

    executed_query = session.execute.call_args[0][0]
    compiled = str(executed_query)
    assert "criado_em" in compiled


@pytest.mark.asyncio
async def test_get_daily_series_retorna_lista_ordenada():
    session = _mock_session_with_result([("2026-01-01", 5), ("2026-01-02", 3)])
    repo = TimeseriesMetricsRepository(session)

    series = await repo.get_daily_series(None, None)

    assert series == [
        DailyCount(data="2026-01-01", quantidade=5),
        DailyCount(data="2026-01-02", quantidade=3),
    ]


@pytest.mark.asyncio
async def test_get_daily_series_vazio_retorna_lista_vazia():
    session = _mock_session_with_result([])
    repo = TimeseriesMetricsRepository(session)

    series = await repo.get_daily_series(None, None)

    assert series == []
