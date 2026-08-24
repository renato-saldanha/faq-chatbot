from unittest.mock import AsyncMock, MagicMock

import pytest

from app.main import app


@pytest.fixture(autouse=True)
def _clear_dependency_overrides():
    """Garante que app.dependency_overrides nunca vaza de um teste de rota HTTP para outro."""
    yield
    app.dependency_overrides.clear()


def make_session_with_scalars(items: list) -> AsyncMock:
    """Mock de AsyncSession cujo `execute(...)` retorna uma lista via `.scalars().all()`.

    Padrão usado pelos repositories que fazem `select(Model)` simples
    (FaqRepository.list_all/get_by_id e similares).
    """
    session = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = items
    session.execute.return_value = result
    return session
