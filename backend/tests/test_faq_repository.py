from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models import Categoria, FaqItem
from app.repositories.faq_repository import FaqRepository
from tests.conftest import make_session_with_scalars


@pytest.mark.asyncio
async def test_list_all_retorna_itens():
    item = FaqItem(id=1, categoria_id=1, pergunta="p", resposta="r", ativo=True)
    session = make_session_with_scalars([item])
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
async def test_create_respeita_ativo_false():
    session = AsyncMock()
    session.add = MagicMock()
    repo = FaqRepository(session)

    item = await repo.create(categoria_id=1, pergunta="p", resposta="r", ativo=False)

    assert item.ativo is False


def _session_com_item(item: FaqItem) -> AsyncMock:
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = item
    session.execute.return_value = result
    return session


@pytest.mark.asyncio
async def test_update_com_pergunta_nova_zera_embedding():
    """Regressão: editar o texto mantinha o vetor do texto antigo e o chat seguia casando com ele."""
    item = FaqItem(id=1, categoria_id=1, pergunta="antiga", resposta="r", ativo=True, embedding=[0.1, 0.2])
    repo = FaqRepository(_session_com_item(item))

    await repo.update(1, categoria_id=1, pergunta="nova", resposta="r", ativo=True)

    assert item.pergunta == "nova"
    assert item.embedding is None


@pytest.mark.asyncio
async def test_update_sem_mudar_pergunta_mantem_embedding():
    item = FaqItem(id=1, categoria_id=1, pergunta="igual", resposta="r", ativo=True, embedding=[0.1, 0.2])
    repo = FaqRepository(_session_com_item(item))

    await repo.update(1, categoria_id=2, pergunta="igual", resposta="outra resposta", ativo=False)

    assert item.embedding == [0.1, 0.2]
    assert item.resposta == "outra resposta"


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
async def test_save_embeddings_commita_quando_ha_itens():
    session = AsyncMock()
    repo = FaqRepository(session)
    item = FaqItem(id=1, categoria_id=1, pergunta="p", resposta="r", ativo=True)

    await repo.save_embeddings([item])

    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_save_embeddings_nao_commita_lista_vazia():
    session = AsyncMock()
    repo = FaqRepository(session)

    await repo.save_embeddings([])

    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_find_nearest_by_embedding_retorna_item_e_distancia():
    item = FaqItem(id=1, categoria_id=1, pergunta="p", resposta="r", ativo=True)
    session = AsyncMock()
    result = MagicMock()
    result.first.return_value = (item, 0.05)
    session.execute.return_value = result
    repo = FaqRepository(session)

    nearest = await repo.find_nearest_by_embedding([1.0, 0.0], [1])

    assert nearest == (item, 0.05)


@pytest.mark.asyncio
async def test_find_nearest_by_embedding_sem_candidatos_retorna_none():
    session = AsyncMock()
    result = MagicMock()
    result.first.return_value = None
    session.execute.return_value = result
    repo = FaqRepository(session)

    nearest = await repo.find_nearest_by_embedding([1.0, 0.0], [])

    assert nearest is None


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
