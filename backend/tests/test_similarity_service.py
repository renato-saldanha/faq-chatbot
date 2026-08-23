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


def _make_faq_repository(items: list, nearest: tuple | None = None) -> AsyncMock:
    repository = AsyncMock()
    repository.list_all.return_value = items
    repository.find_nearest_by_embedding.return_value = nearest
    return repository


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
        faq_repository = _make_faq_repository([item])

        result = await service.find_best_match("Como eu cadastro uma conta nova?", faq_repository)

        assert result is not None
        assert result.faq_item_id == 1
        assert result.categoria == "Conta"
        assert result.score >= 0.6

    @pytest.mark.asyncio
    async def test_sem_match_score_baixo(self) -> None:
        service = FuzzySimilarityService()
        service._threshold = 0.6
        item = _make_faq_item(1, "Como cancelo minha conta?", "Entre em contato com o suporte.", "Conta")
        faq_repository = _make_faq_repository([item])

        result = await service.find_best_match("Qual a previsão do tempo amanhã em Marte?", faq_repository)

        assert result is None

    @pytest.mark.asyncio
    async def test_pergunta_vazia(self) -> None:
        service = FuzzySimilarityService()
        faq_repository = _make_faq_repository([])

        result = await service.find_best_match("   ", faq_repository)

        assert result is None


class TestEmbeddingSimilarityServiceEnsureEmbeddings:
    @pytest.mark.asyncio
    async def test_calcula_apenas_itens_sem_embedding(self) -> None:
        client = _make_openai_client([1.0, 0.0])
        service = EmbeddingSimilarityService(client)
        item_sem_embedding = _make_faq_item(1, "Como cancelo minha conta?", "Resposta.", "Conta", embedding=None)
        item_com_embedding = _make_faq_item(2, "Como troco meu email?", "Resposta.", "Conta", embedding=[0.5, 0.5])
        faq_repository = AsyncMock()

        await service.ensure_embeddings([item_sem_embedding, item_com_embedding], faq_repository)

        assert item_sem_embedding.embedding == [1.0, 0.0]
        assert item_com_embedding.embedding == [0.5, 0.5]
        client.embeddings.create.assert_called_once()
        faq_repository.save_embeddings.assert_awaited_once_with([item_sem_embedding])

    @pytest.mark.asyncio
    async def test_nao_commita_quando_todos_ja_tem_embedding(self) -> None:
        client = _make_openai_client([1.0, 0.0])
        service = EmbeddingSimilarityService(client)
        item = _make_faq_item(1, "Como cancelo minha conta?", "Resposta.", "Conta", embedding=[0.1, 0.2])
        faq_repository = AsyncMock()

        await service.ensure_embeddings([item], faq_repository)

        client.embeddings.create.assert_not_called()
        faq_repository.save_embeddings.assert_awaited_once_with([])

    @pytest.mark.asyncio
    async def test_pergunta_vazia_nao_chama_openai(self) -> None:
        client = _make_openai_client([1.0, 0.0])
        service = EmbeddingSimilarityService(client)
        faq_repository = AsyncMock()

        result = await service.find_best_match("   ", faq_repository)

        assert result is None
        client.embeddings.create.assert_not_called()


class TestEmbeddingSimilarityServiceFindBestMatch:
    @pytest.mark.asyncio
    async def test_match_via_distancia_de_cosseno(self) -> None:
        client = _make_openai_client([1.0, 0.0])
        service = EmbeddingSimilarityService(client)
        service._threshold = 0.5
        item = _make_faq_item(
            1, "Como cadastro uma conta nova?", "Acesse a página de cadastro.", "Conta", embedding=[1.0, 0.0]
        )
        faq_repository = _make_faq_repository([item], nearest=(item, 0.05))

        result = await service.find_best_match("Como crio uma conta?", faq_repository)

        assert result is not None
        assert result.faq_item_id == 1
        assert result.categoria == "Conta"
        assert result.score == pytest.approx(0.95)
        faq_repository.find_nearest_by_embedding.assert_awaited_once_with([1.0, 0.0], [1])

    @pytest.mark.asyncio
    async def test_score_abaixo_do_threshold_retorna_none(self) -> None:
        client = _make_openai_client([1.0, 0.0])
        service = EmbeddingSimilarityService(client)
        service._threshold = 0.6
        item = _make_faq_item(1, "Como cadastro uma conta nova?", "Resposta.", "Conta", embedding=[1.0, 0.0])
        faq_repository = _make_faq_repository([item], nearest=(item, 0.9))

        result = await service.find_best_match("pergunta bem diferente", faq_repository)

        assert result is None

    @pytest.mark.asyncio
    async def test_sem_itens_ativos_retorna_none(self) -> None:
        client = _make_openai_client([1.0, 0.0])
        service = EmbeddingSimilarityService(client)
        faq_repository = _make_faq_repository([])

        result = await service.find_best_match("Como cancelo minha conta?", faq_repository)

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
        faq_repository = _make_faq_repository([item])

        result = await service.find_best_match("Como cadastro uma conta nova?", faq_repository)

        assert result is not None
        assert result.faq_item_id == 1
        assert result.categoria == "Conta"
        assert result.score > 0.9

    @pytest.mark.asyncio
    async def test_pergunta_vazia(self) -> None:
        client = _make_openai_client([1.0, 0.0])
        service = HybridSimilarityService(FuzzySimilarityService(), EmbeddingSimilarityService(client))
        faq_repository = _make_faq_repository([])

        result = await service.find_best_match("   ", faq_repository)

        assert result is None

    @pytest.mark.asyncio
    async def test_sem_itens_ativos_retorna_none(self) -> None:
        client = _make_openai_client([1.0, 0.0])
        service = HybridSimilarityService(FuzzySimilarityService(), EmbeddingSimilarityService(client))
        faq_repository = _make_faq_repository([])

        result = await service.find_best_match("Como cancelo minha conta?", faq_repository)

        assert result is None
