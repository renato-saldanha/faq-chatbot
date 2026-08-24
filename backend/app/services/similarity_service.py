import logging
import re
import unicodedata
from abc import ABC, abstractmethod
from dataclasses import dataclass

from openai import APIError, AsyncOpenAI
from rapidfuzz import fuzz

from app.config import get_settings
from app.models import FaqItem
from app.repositories.faq_repository import FaqRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MatchResult:
    faq_item_id: int
    categoria_id: int
    resposta: str
    categoria: str
    score: float


def normalize_text(texto: str) -> str:
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^\w\s]", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


class SimilarityService(ABC):
    @abstractmethod
    async def find_best_match(self, pergunta: str, faq_repository: FaqRepository) -> MatchResult | None: ...

    @abstractmethod
    async def vector_for(self, texto: str) -> object: ...


class FuzzySimilarityService(SimilarityService):
    """Protótipo A do PRD §5 — comparação léxica via rapidfuzz, sem custo de API externa."""

    def __init__(self) -> None:
        self._threshold = get_settings().similarity_threshold

    async def vector_for(self, texto: str) -> str:
        return normalize_text(texto)

    async def find_best_match(self, pergunta: str, faq_repository: FaqRepository) -> MatchResult | None:
        pergunta_normalizada = normalize_text(pergunta)
        if not pergunta_normalizada:
            return None

        itens = await faq_repository.list_all(only_active=True)
        if not itens:
            return None

        best_item: FaqItem | None = None
        best_score = 0.0
        for item in itens:
            score = fuzz.token_sort_ratio(pergunta_normalizada, normalize_text(item.pergunta)) / 100.0
            if score > best_score:
                best_score = score
                best_item = item

        if best_item is None or best_score < self._threshold:
            return None

        return MatchResult(
            faq_item_id=best_item.id,
            categoria_id=best_item.categoria_id,
            resposta=best_item.resposta,
            categoria=best_item.categoria.nome,
            score=best_score,
        )


class EmbeddingSimilarityService(SimilarityService):
    """Protótipo B do PRD §5 — comparação semântica via embeddings da OpenAI.

    Cache de embedding: FaqItem.embedding é calculado e persistido na primeira
    consulta que o encontrar vazio (lazy population) — não recalcula a cada
    seed/boot, só quando o item ainda não tem vetor salvo. Comparação por
    cosseno é feita no Postgres via pgvector (cosine_distance), não em Python.
    """

    def __init__(self, client: AsyncOpenAI) -> None:
        self._client = client
        self._model = get_settings().openai_model
        self._threshold = get_settings().similarity_threshold

    async def vector_for(self, texto: str) -> list[float]:
        texto_normalizado = normalize_text(texto)
        response = await self._client.embeddings.create(model=self._model, input=texto_normalizado)
        return response.data[0].embedding

    async def ensure_embeddings(self, itens: list[FaqItem], faq_repository: FaqRepository) -> None:
        """Calcula e persiste o embedding de cada item que ainda não tem (cache lazy)."""
        pendentes = [item for item in itens if item.embedding is None]
        for item in pendentes:
            item.embedding = await self.vector_for(item.pergunta)
        await faq_repository.save_embeddings(pendentes)

    async def find_best_match(self, pergunta: str, faq_repository: FaqRepository) -> MatchResult | None:
        pergunta_normalizada = normalize_text(pergunta)
        if not pergunta_normalizada:
            return None

        itens = await faq_repository.list_all(only_active=True)
        if not itens:
            return None

        await self.ensure_embeddings(itens, faq_repository)

        query_vector = await self.vector_for(pergunta)

        nearest = await faq_repository.find_nearest_by_embedding(query_vector, [item.id for item in itens])
        if nearest is None:
            return None

        best_item, distance = nearest
        score = 1.0 - distance
        if score < self._threshold:
            return None

        categoria = next(item.categoria for item in itens if item.id == best_item.id)
        return MatchResult(
            faq_item_id=best_item.id,
            categoria_id=best_item.categoria_id,
            resposta=best_item.resposta,
            categoria=categoria.nome,
            score=score,
        )


class HybridSimilarityService(SimilarityService):
    """Protótipo C do PRD §5 — combina os scores de fuzzy e embedding.

    score_final = alpha * score_embedding + (1 - alpha) * score_trigram,
    calculado para cada FaqItem ativo (não reaproveita find_best_match de
    cada serviço isolado — precisamos do score de AMBOS pro MESMO conjunto
    de candidatos, não só o vencedor de cada busca independente). Reaproveita
    normalize_text (fuzzy) e vector_for/embedding persistido (embedding) de
    cada serviço injetado, evitando duplicar a lógica de comparação em si.
    """

    ALPHA = 0.6

    def __init__(self, fuzzy: FuzzySimilarityService, embedding: EmbeddingSimilarityService) -> None:
        self._fuzzy = fuzzy
        self._embedding = embedding
        self._threshold = get_settings().similarity_threshold

    async def vector_for(self, texto: str) -> list[float]:
        return await self._embedding.vector_for(texto)

    async def find_best_match(self, pergunta: str, faq_repository: FaqRepository) -> MatchResult | None:
        pergunta_normalizada = normalize_text(pergunta)
        if not pergunta_normalizada:
            return None

        itens = await faq_repository.list_all(only_active=True)
        if not itens:
            return None

        await self._embedding.ensure_embeddings(itens, faq_repository)
        query_vector = await self.vector_for(pergunta)

        best_item: FaqItem | None = None
        best_score = 0.0
        for item in itens:
            score_fuzzy = fuzz.token_sort_ratio(pergunta_normalizada, normalize_text(item.pergunta)) / 100.0
            score_embedding = (
                self._cosine_similarity(query_vector, item.embedding) if item.embedding is not None else 0.0
            )
            score_final = self.ALPHA * score_embedding + (1 - self.ALPHA) * score_fuzzy
            if score_final > best_score:
                best_score = score_final
                best_item = item

        if best_item is None or best_score < self._threshold:
            return None

        return MatchResult(
            faq_item_id=best_item.id,
            categoria_id=best_item.categoria_id,
            resposta=best_item.resposta,
            categoria=best_item.categoria.nome,
            score=best_score,
        )

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b, strict=True))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(y * y for y in b) ** 0.5
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)


class FallbackSimilarityService(SimilarityService):
    """Envolve um backend que depende da API OpenAI (embedding/hybrid) e degrada para fuzzy se ela falhar.

    Falha de rede, timeout, rate limit ou chave inválida (openai.APIError e
    subclasses) não devem derrubar o chat — melhor responder com o backend
    mais fraco (fuzzy) do que retornar 500 pro usuário final.
    """

    def __init__(self, primary: SimilarityService, fuzzy: FuzzySimilarityService) -> None:
        self._primary = primary
        self._fuzzy = fuzzy

    async def vector_for(self, texto: str) -> object:
        try:
            return await self._primary.vector_for(texto)
        except APIError:
            logger.warning("Falha na API OpenAI em vector_for, usando fallback fuzzy", exc_info=True)
            return await self._fuzzy.vector_for(texto)

    async def find_best_match(self, pergunta: str, faq_repository: FaqRepository) -> MatchResult | None:
        try:
            return await self._primary.find_best_match(pergunta, faq_repository)
        except APIError:
            logger.warning("Falha na API OpenAI em find_best_match, usando fallback fuzzy", exc_info=True)
            return await self._fuzzy.find_best_match(pergunta, faq_repository)
