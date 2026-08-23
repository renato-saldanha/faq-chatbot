from unittest.mock import AsyncMock, MagicMock

import pytest

from app.repositories.faq_metrics_repository import (
    CategoryBreakdown,
    FaqMetricsRepository,
    TopQuestion,
)


def _mock_session_with_rows(rows):
    session = MagicMock()
    result = MagicMock()
    result.all = MagicMock(return_value=rows)
    session.execute = AsyncMock(return_value=result)
    return session


@pytest.mark.asyncio
async def test_get_top_questions_retorna_ordenado_por_quantidade():
    session = _mock_session_with_rows([(1, "Como cadastro uma conta?", 8), (2, "Como cancelo?", 3)])
    repo = FaqMetricsRepository(session)

    result = await repo.get_top_questions(None, None, limit=10)

    assert result == [
        TopQuestion(faq_item_id=1, pergunta="Como cadastro uma conta?", quantidade=8),
        TopQuestion(faq_item_id=2, pergunta="Como cancelo?", quantidade=3),
    ]


@pytest.mark.asyncio
async def test_get_top_questions_aplica_limit():
    session = _mock_session_with_rows([(1, "pergunta", 5)])
    repo = FaqMetricsRepository(session)

    await repo.get_top_questions(None, None, limit=3)

    executed_query = session.execute.call_args[0][0]
    assert "LIMIT" in str(executed_query).upper()


@pytest.mark.asyncio
async def test_get_top_questions_vazio():
    session = _mock_session_with_rows([])
    repo = FaqMetricsRepository(session)

    result = await repo.get_top_questions(None, None)

    assert result == []


@pytest.mark.asyncio
async def test_get_category_breakdown_retorna_ordenado():
    session = _mock_session_with_rows([("Conta", 12), ("Pagamentos", 7)])
    repo = FaqMetricsRepository(session)

    result = await repo.get_category_breakdown(None, None)

    assert result == [
        CategoryBreakdown(categoria="Conta", quantidade=12),
        CategoryBreakdown(categoria="Pagamentos", quantidade=7),
    ]


@pytest.mark.asyncio
async def test_get_category_breakdown_vazio():
    session = _mock_session_with_rows([])
    repo = FaqMetricsRepository(session)

    result = await repo.get_category_breakdown(None, None)

    assert result == []
