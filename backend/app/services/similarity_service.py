import re
import unicodedata
from abc import ABC, abstractmethod
from dataclasses import dataclass

from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import FaqItem


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
    async def find_best_match(self, pergunta: str, session: AsyncSession) -> MatchResult | None: ...

    @abstractmethod
    def vector_for(self, texto: str) -> object: ...


class FuzzySimilarityService(SimilarityService):
    """Protótipo A do PRD §5 — comparação léxica via rapidfuzz, sem custo de API externa."""

    def __init__(self) -> None:
        self._threshold = get_settings().similarity_threshold

    def vector_for(self, texto: str) -> str:
        return normalize_text(texto)

    async def find_best_match(self, pergunta: str, session: AsyncSession) -> MatchResult | None:
        pergunta_normalizada = normalize_text(pergunta)
        if not pergunta_normalizada:
            return None

        result = await session.execute(
            select(FaqItem).where(FaqItem.ativo.is_(True)).join(FaqItem.categoria)
        )
        itens = result.scalars().all()
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
