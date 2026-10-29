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


def test_otp_store_bloqueia_brute_force_de_verificacao():
    otp_store = OtpStore()
    email = "admin@example.com"
    code = otp_store.generate(email)

    for _ in range(5):
        assert otp_store.verify(email, "000000") is False

    # código correto, mas o limite de tentativas de verificação já foi atingido
    assert otp_store.verify(email, code) is False


def test_demo_otp_store_valida_em_outra_instancia():
    from app.auth.otp_store import DemoOtpStore

    code = DemoOtpStore("segredo").generate("admin@demo.test")

    assert DemoOtpStore("segredo").verify("Admin@Demo.test", code) is True
    assert DemoOtpStore("outro-segredo").verify("admin@demo.test", code) is False
    assert DemoOtpStore("segredo").verify("admin@demo.test", "abc") is False


def test_demo_otp_store_aceita_janela_anterior_e_rejeita_antiga(monkeypatch):
    from app.auth import otp_store as module

    store = module.DemoOtpStore("segredo")
    monkeypatch.setattr(module.time, "time", lambda: 1_000_000.0)
    code = store.generate("admin@demo.test")

    monkeypatch.setattr(module.time, "time", lambda: 1_000_000.0 + 5 * 60)
    assert store.verify("admin@demo.test", code) is True

    monkeypatch.setattr(module.time, "time", lambda: 1_000_000.0 + 10 * 60)
    assert store.verify("admin@demo.test", code) is False


@pytest.mark.asyncio
async def test_request_otp_modo_demo_devolve_codigo_valido():
    from app.auth.otp_store import DemoOtpStore

    settings = Settings(admin_email="admin@demo.test", demo_mode=True)
    service = AuthService(DemoOtpStore("segredo"), settings)

    code = await service.request_otp("admin@demo.test")

    assert code is not None
    assert service.verify_otp("admin@demo.test", code) is not None
    assert await service.request_otp("outro@demo.test") is None


@pytest.mark.asyncio
async def test_request_otp_sem_modo_demo_nao_devolve_codigo():
    service = AuthService(OtpStore(), _settings())

    assert await service.request_otp("admin@example.com") is None
