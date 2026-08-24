from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import decode_session_token
from app.db import get_db_session
from app.repositories.faq_repository import FaqRepository


def require_admin_session(session: str | None = Cookie(default=None)) -> str:
    """Dependency que protege rotas de admin (/api/faq, /api/metrics).

    Valida o cookie httpOnly de sessão; 401 se ausente/inválido.
    """
    if session is None:
        raise HTTPException(status_code=401, detail="Sessão ausente")
    email = decode_session_token(session)
    if email is None:
        raise HTTPException(status_code=401, detail="Sessão inválida ou expirada")
    return email


def get_faq_repository(session: AsyncSession = Depends(get_db_session)) -> FaqRepository:
    return FaqRepository(session)
