import time

import pytest

from app.auth.otp_store import OtpStore
from app.config import Settings
from app.services.auth_service import AuthService


def _settings(admin_email: str = "admin@example.com") -> Settings:
    return Settings(admin_email=admin_email, smtp_host="")


@pytest.mark.asyncio
async def test_request_otp_email_correto_gera_codigo():
    otp_store = OtpStore()
    service = AuthService(otp_store, _settings())

    await service.request_otp("admin@example.com")

    assert otp_store.verify("admin@example.com", otp_store._codes["admin@example.com"])


@pytest.mark.asyncio
async def test_request_otp_email_incorreto_nao_gera_codigo():
    otp_store = OtpStore()
    service = AuthService(otp_store, _settings())

    await service.request_otp("outro@example.com")

    assert "outro@example.com" not in otp_store._codes


def test_verify_otp_codigo_valido_retorna_token():
    otp_store = OtpStore()
    settings = _settings()
    service = AuthService(otp_store, settings)
    code = otp_store.generate("admin@example.com")

    token = service.verify_otp("admin@example.com", code)

    assert token is not None
    assert isinstance(token, str)


def test_verify_otp_codigo_invalido_retorna_none():
    otp_store = OtpStore()
    service = AuthService(otp_store, _settings())
    otp_store.generate("admin@example.com")

    token = service.verify_otp("admin@example.com", "000000")

    assert token is None


def test_verify_otp_email_incorreto_retorna_none():
    otp_store = OtpStore()
    service = AuthService(otp_store, _settings())
    code = otp_store.generate("admin@example.com")

    token = service.verify_otp("outro@example.com", code)

    assert token is None


def test_otp_store_single_use():
    otp_store = OtpStore()
    code = otp_store.generate("admin@example.com")

    assert otp_store.verify("admin@example.com", code) is True
    assert otp_store.verify("admin@example.com", code) is False


def test_otp_store_expira_apos_ttl():
    from cachetools import TTLCache

    otp_store = OtpStore()
    otp_store._codes = TTLCache(maxsize=1000, ttl=0.01)
    code = otp_store.generate("admin@example.com")
    time.sleep(0.05)

    assert otp_store.verify("admin@example.com", code) is False


def test_otp_store_rate_limit_bloqueia_apos_limite():
    otp_store = OtpStore()
    email = "admin@example.com"

    for _ in range(3):
        assert otp_store.can_request(email) is True
        otp_store.record_request(email)

    assert otp_store.can_request(email) is False
