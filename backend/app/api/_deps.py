from fastapi import Cookie, HTTPException

from app.auth.jwt import decode_session_token


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
