from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models import Categoria, FaqItem
from app.repositories.faq_repository import FaqRepository


def _make_session_with_execute_result(items: list) -> AsyncMock:
    session = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = items
    session.execute.return_value = result
    return session


@pytest.mark.asyncio
async def test_list_all_retorna_itens():
    item = FaqItem(id=1, categoria_id=1, pergunta="p", resposta="r", ativo=True)
    session = _make_session_with_execute_result([item])
    repo = FaqRepository(session)

    result = await repo.list_all()

    assert result == [item]


@pytest.mark.asyncio
async def test_get_by_id_encontrado():
    item = FaqItem(id=1, categoria_id=1, pergunta="p", resposta="r", ativo=True)
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = item
    session.execute.return_value = result
    repo = FaqRepository(session)

    found = await repo.get_by_id(1)

    assert found is item


@pytest.mark.asyncio
async def test_get_by_id_nao_encontrado():
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute.return_value = result
    repo = FaqRepository(session)

    found = await repo.get_by_id(999)

    assert found is None


@pytest.mark.asyncio
async def test_create_adiciona_e_commita():
    session = AsyncMock()
    repo = FaqRepository(session)

    await repo.create(categoria_id=1, pergunta="p", resposta="r")

    session.add.assert_called_once()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_item_inexistente_retorna_false():
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute.return_value = result
    repo = FaqRepository(session)

    deleted = await repo.delete(999)

    assert deleted is False
    session.delete.assert_not_called()


@pytest.mark.asyncio
async def test_create_categoria():
    session = AsyncMock()
    repo = FaqRepository(session)

    await repo.create_categoria(nome="Suporte", slug="suporte")

    session.add.assert_called_once()
    added = session.add.call_args[0][0]
    assert isinstance(added, Categoria)
    assert added.nome == "Suporte"
    assert added.slug == "suporte"
