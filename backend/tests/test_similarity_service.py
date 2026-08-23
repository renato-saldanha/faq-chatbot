from typing import Any
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest

from app.services.similarity_service import (
    EmbeddingSimilarityService,
    FuzzySimilarityService,
    HybridSimilarityService,
    normalize_text,
)


def _make_faq_item(
    id_: int,
    pergunta: str,
    resposta: str,
    categoria_nome: str,
    embedding: "list[float] | np.ndarray[Any, np.dtype[Any]] | None" = None,
) -> MagicMock:
    item = MagicMock()
    item.id = id_
    item.categoria_id = id_
    item.pergunta = pergunta
    item.resposta = resposta
    item.ativo = True
    item.embedding = embedding
    item.categoria = MagicMock()
    item.categoria.nome = categoria_nome
    return item


def _make_session_with_items(items: list) -> AsyncMock:
    session = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = items
    session.execute.return_value = result
    return session


def _make_openai_client(embedding: list[float]) -> AsyncMock:
    client = AsyncMock()
    response = MagicMock()
    response.data = [MagicMock(embedding=embedding)]
    client.embeddings.create.return_value = response
    return client


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


class TestEmbeddingSimilarityServiceEnsureEmbeddings:
    @pytest.mark.asyncio
    async def test_calcula_apenas_itens_sem_embedding(self) -> None:
        client = _make_openai_client([1.0, 0.0])
        service = EmbeddingSimilarityService(client)
        item_sem_embedding = _make_faq_item(1, "Como cancelo minha conta?", "Resposta.", "Conta", embedding=None)
        item_com_embedding = _make_faq_item(2, "Como troco meu email?", "Resposta.", "Conta", embedding=[0.5, 0.5])
        session = AsyncMock()

        await service.ensure_embeddings([item_sem_embedding, item_com_embedding], session)

        assert item_sem_embedding.embedding == [1.0, 0.0]
        assert item_com_embedding.embedding == [0.5, 0.5]
        client.embeddings.create.assert_called_once()
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_nao_commita_quando_todos_ja_tem_embedding(self) -> None:
        client = _make_openai_client([1.0, 0.0])
        service = EmbeddingSimilarityService(client)
        item = _make_faq_item(1, "Como cancelo minha conta?", "Resposta.", "Conta", embedding=[0.1, 0.2])
        session = AsyncMock()

        await service.ensure_embeddings([item], session)

        client.embeddings.create.assert_not_called()
        session.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_pergunta_vazia_nao_chama_openai(self) -> None:
        client = _make_openai_client([1.0, 0.0])
        service = EmbeddingSimilarityService(client)
        session = AsyncMock()

        result = await service.find_best_match("   ", session)

        assert result is None
        client.embeddings.create.assert_not_called()


class TestHybridSimilarityServiceCosineSimilarity:
    def test_vetores_identicos_tem_similaridade_um(self) -> None:
        assert HybridSimilarityService._cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)

    def test_vetores_ortogonais_tem_similaridade_zero(self) -> None:
        assert HybridSimilarityService._cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)

    def test_vetor_nulo_retorna_zero_sem_dividir_por_zero(self) -> None:
        assert HybridSimilarityService._cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0


class TestHybridSimilarityServiceFindBestMatch:
    @pytest.mark.asyncio
    async def test_combina_score_fuzzy_e_embedding_do_mesmo_item(self) -> None:
        client = _make_openai_client([1.0, 0.0])
        embedding_service = EmbeddingSimilarityService(client)
        fuzzy_service = FuzzySimilarityService()
        service = HybridSimilarityService(fuzzy_service, embedding_service)
        service._threshold = 0.1

        item = _make_faq_item(
            1,
            "Como cadastro uma conta nova?",
            "Acesse a página de cadastro.",
            "Conta",
            embedding=np.array([1.0, 0.0]),
        )
        session = _make_session_with_items([item])

        result = await service.find_best_match("Como cadastro uma conta nova?", session)

        assert result is not None
        assert result.faq_item_id == 1
        assert result.categoria == "Conta"
        assert result.score > 0.9

    @pytest.mark.asyncio
    async def test_pergunta_vazia(self) -> None:
        client = _make_openai_client([1.0, 0.0])
        service = HybridSimilarityService(FuzzySimilarityService(), EmbeddingSimilarityService(client))
        session = _make_session_with_items([])

        result = await service.find_best_match("   ", session)

        assert result is None

    @pytest.mark.asyncio
    async def test_sem_itens_ativos_retorna_none(self) -> None:
        client = _make_openai_client([1.0, 0.0])
        service = HybridSimilarityService(FuzzySimilarityService(), EmbeddingSimilarityService(client))
        session = _make_session_with_items([])

        result = await service.find_best_match("Como cancelo minha conta?", session)

        assert result is None
