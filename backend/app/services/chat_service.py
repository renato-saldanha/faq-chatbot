from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.interacao_repository import InteracaoRepository
from app.services.similarity_service import SimilarityService

FALLBACK_MESSAGE = "Não encontrei uma resposta para sua pergunta. Tente reformular ou entre em contato com o suporte."


class ChatResponse(BaseModel):
    resposta: str
    faq_item_id: int | None
    categoria: str | None
    sem_resposta: bool
    score: float | None


class ChatService:
    def __init__(
        self,
        similarity_service: SimilarityService,
        interacao_repository: InteracaoRepository,
        session: AsyncSession,
    ) -> None:
        self._similarity_service = similarity_service
        self._interacao_repository = interacao_repository
        self._session = session

    async def ask(self, pergunta: str) -> ChatResponse:
        match = await self._similarity_service.find_best_match(pergunta, self._session)

        if match is None:
            await self._interacao_repository.create(
                pergunta_usuario=pergunta,
                faq_item_id=None,
                categoria_id=None,
                score=None,
                sem_resposta=True,
            )
            return ChatResponse(
                resposta=FALLBACK_MESSAGE,
                faq_item_id=None,
                categoria=None,
                sem_resposta=True,
                score=None,
            )

        await self._interacao_repository.create(
            pergunta_usuario=pergunta,
            faq_item_id=match.faq_item_id,
            categoria_id=match.categoria_id,
            score=match.score,
            sem_resposta=False,
        )
        return ChatResponse(
            resposta=match.resposta,
            faq_item_id=match.faq_item_id,
            categoria=match.categoria,
            sem_resposta=False,
            score=match.score,
        )
