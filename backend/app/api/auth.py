from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from app.auth.otp_store import OtpStore, get_otp_store
from app.config import Settings, get_settings
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])

_SESSION_COOKIE_NAME = "session"


class OtpRequestBody(BaseModel):
    email: str


class OtpVerifyBody(BaseModel):
    email: str
    codigo: str


class AuthOkResponse(BaseModel):
    authenticated: bool


def get_auth_service(
    otp_store: OtpStore = Depends(get_otp_store),
    settings: Settings = Depends(get_settings),
) -> AuthService:
    return AuthService(otp_store, settings)


@router.post("/otp/request", response_model=AuthOkResponse)
async def request_otp(body: OtpRequestBody, service: AuthService = Depends(get_auth_service)) -> AuthOkResponse:
    await service.request_otp(body.email)
    return AuthOkResponse(authenticated=False)


@router.post("/otp/verify", response_model=AuthOkResponse)
async def verify_otp(
    body: OtpVerifyBody,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> AuthOkResponse:
    token = service.verify_otp(body.email, body.codigo)
    if token is None:
        raise HTTPException(status_code=401, detail="Código inválido ou expirado")

    response.set_cookie(
        key=_SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=8 * 60 * 60,
    )
    return AuthOkResponse(authenticated=True)


@router.post("/logout", response_model=AuthOkResponse)
async def logout(response: Response) -> AuthOkResponse:
    response.delete_cookie(_SESSION_COOKIE_NAME)
    return AuthOkResponse(authenticated=False)
