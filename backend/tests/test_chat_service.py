from unittest.mock import AsyncMock

import pytest

from app.services.chat_service import FALLBACK_MESSAGE, ChatService
from app.services.similarity_service import MatchResult


class TestChatServiceAsk:
    @pytest.mark.asyncio
    async def test_com_match_retorna_resposta_e_grava_interacao(self) -> None:
        similarity_service = AsyncMock()
        similarity_service.find_best_match.return_value = MatchResult(
            faq_item_id=1, resposta="Acesse a página de cadastro.", categoria="Conta", score=0.95
        )
        interacao_repository = AsyncMock()
        session = AsyncMock()

        service = ChatService(similarity_service, interacao_repository, session)
        response = await service.ask("Como cadastro uma conta?")

        assert response.sem_resposta is False
        assert response.resposta == "Acesse a página de cadastro."
        assert response.faq_item_id == 1
        assert response.score == 0.95
        interacao_repository.create.assert_awaited_once()
        _, kwargs = interacao_repository.create.await_args
        assert kwargs["sem_resposta"] is False
        assert kwargs["faq_item_id"] == 1

    @pytest.mark.asyncio
    async def test_sem_match_retorna_fallback_e_grava_interacao(self) -> None:
        similarity_service = AsyncMock()
        similarity_service.find_best_match.return_value = None
        interacao_repository = AsyncMock()
        session = AsyncMock()

        service = ChatService(similarity_service, interacao_repository, session)
        response = await service.ask("pergunta sem relação nenhuma com a base")

        assert response.sem_resposta is True
        assert response.resposta == FALLBACK_MESSAGE
        assert response.faq_item_id is None
        interacao_repository.create.assert_awaited_once()
        _, kwargs = interacao_repository.create.await_args
        assert kwargs["sem_resposta"] is True
        assert kwargs["faq_item_id"] is None
