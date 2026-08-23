from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.similarity_service import FuzzySimilarityService, normalize_text


def _make_faq_item(id_: int, pergunta: str, resposta: str, categoria_nome: str) -> MagicMock:
    item = MagicMock()
    item.id = id_
    item.pergunta = pergunta
    item.resposta = resposta
    item.ativo = True
    item.categoria = MagicMock()
    item.categoria.nome = categoria_nome
    return item


def _make_session_with_items(items: list) -> AsyncMock:
    session = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = items
    session.execute.return_value = result
    return session


class TestNormalizeText:
    def test_remove_acentos_e_pontuacao(self) -> None:
        assert normalize_text("Como cancelo minha conta?") == "como cancelo minha conta"
        assert normalize_text("É possível?") == "e possivel"


class TestFuzzySimilarityServiceFindBestMatch:
    @pytest.mark.asyncio
    async def test_match_obvio(self) -> None:
        service = FuzzySimilarityService()
        service._threshold = 0.6
        item = _make_faq_item(1, "Como eu cadastro uma conta nova?", "Acesse a página de cadastro.", "Conta")
        session = _make_session_with_items([item])

        result = await service.find_best_match("Como eu cadastro uma conta nova?", session)

        assert result is not None
        assert result.faq_item_id == 1
        assert result.categoria == "Conta"
        assert result.score >= 0.6

    @pytest.mark.asyncio
    async def test_sem_match_score_baixo(self) -> None:
        service = FuzzySimilarityService()
        service._threshold = 0.6
        item = _make_faq_item(1, "Como cancelo minha conta?", "Entre em contato com o suporte.", "Conta")
        session = _make_session_with_items([item])

        result = await service.find_best_match("Qual a previsão do tempo amanhã em Marte?", session)

        assert result is None

    @pytest.mark.asyncio
    async def test_pergunta_vazia(self) -> None:
        service = FuzzySimilarityService()
        session = _make_session_with_items([])

        result = await service.find_best_match("   ", session)

        assert result is None
