from functools import lru_cache

from fastapi import APIRouter, Depends
from openai import AsyncOpenAI
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.api._deps import get_faq_repository
from app.config import get_settings
from app.db import get_db_session
from app.repositories.faq_repository import FaqRepository
from app.repositories.interacao_repository import InteracaoRepository
from app.services.chat_service import ChatResponse, ChatService
from app.services.similarity_service import (
    EmbeddingSimilarityService,
    FuzzySimilarityService,
    HybridSimilarityService,
    SimilarityService,
)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@lru_cache
def get_similarity_service() -> SimilarityService:
    """Instância única por processo — o backend não guarda estado de request (repository é injetado por chamada)."""
    backend = get_settings().similarity_backend
    if backend == "fuzzy":
        return FuzzySimilarityService()
    if backend == "embedding":
        client = AsyncOpenAI(api_key=get_settings().openai_api_key)
        return EmbeddingSimilarityService(client)
    if backend == "hybrid":
        client = AsyncOpenAI(api_key=get_settings().openai_api_key)
        return HybridSimilarityService(FuzzySimilarityService(), EmbeddingSimilarityService(client))
    raise ValueError(f"SIMILARITY_BACKEND inválido: {backend!r}")


class ChatAskRequest(BaseModel):
    pergunta: str

    @field_validator("pergunta")
    @classmethod
    def pergunta_nao_pode_ser_vazia(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("pergunta não pode ser vazia")
        return v


def get_interacao_repository(session: AsyncSession = Depends(get_db_session)) -> InteracaoRepository:
    return InteracaoRepository(session)


def get_chat_service(
    faq_repository: FaqRepository = Depends(get_faq_repository),
    interacao_repository: InteracaoRepository = Depends(get_interacao_repository),
) -> ChatService:
    similarity_service = get_similarity_service()
    return ChatService(similarity_service, interacao_repository, faq_repository)


@router.post("/ask", response_model=ChatResponse)
async def ask(request: ChatAskRequest, chat_service: ChatService = Depends(get_chat_service)) -> ChatResponse:
    return await chat_service.ask(request.pergunta)
