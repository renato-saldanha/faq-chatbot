from unittest.mock import AsyncMock, MagicMock


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
