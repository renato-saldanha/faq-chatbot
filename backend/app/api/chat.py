from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.repositories.interacao_repository import InteracaoRepository
from app.services.chat_service import ChatResponse, ChatService
from app.services.similarity_service import FuzzySimilarityService

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatAskRequest(BaseModel):
    pergunta: str

    @field_validator("pergunta")
    @classmethod
    def pergunta_nao_pode_ser_vazia(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("pergunta não pode ser vazia")
        return v


def get_chat_service(session: AsyncSession = Depends(get_db_session)) -> ChatService:
    similarity_service = FuzzySimilarityService()
    interacao_repository = InteracaoRepository(session)
    return ChatService(similarity_service, interacao_repository, session)


@router.post("/ask", response_model=ChatResponse)
async def ask(request: ChatAskRequest, chat_service: ChatService = Depends(get_chat_service)) -> ChatResponse:
    return await chat_service.ask(request.pergunta)
