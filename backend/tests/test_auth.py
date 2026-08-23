from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from app.api.auth import get_auth_service
from app.main import app


def _override_auth_service() -> AsyncMock:
    service = AsyncMock()
    service.verify_otp = MagicMock()
    app.dependency_overrides[get_auth_service] = lambda: service
    return service


class TestRequestOtp:
    def test_retorna_200_authenticated_false(self) -> None:
        service = _override_auth_service()
        try:
            client = TestClient(app)
            response = client.post("/api/auth/otp/request", json={"email": "admin@example.com"})

            assert response.status_code == 200
            assert response.json() == {"authenticated": False}
            service.request_otp.assert_awaited_once_with("admin@example.com")
        finally:
            app.dependency_overrides.clear()


class TestVerifyOtp:
    def test_codigo_valido_seta_cookie_e_retorna_200(self) -> None:
        service = _override_auth_service()
        service.verify_otp.return_value = "um-jwt-qualquer"
        try:
            client = TestClient(app)
            response = client.post("/api/auth/otp/verify", json={"email": "admin@example.com", "codigo": "123456"})

            assert response.status_code == 200
            assert response.json() == {"authenticated": True}
            assert "session" in response.cookies
        finally:
            app.dependency_overrides.clear()

    def test_codigo_invalido_retorna_401(self) -> None:
        service = _override_auth_service()
        service.verify_otp.return_value = None
        try:
            client = TestClient(app)
            response = client.post("/api/auth/otp/verify", json={"email": "admin@example.com", "codigo": "000000"})

            assert response.status_code == 401
            assert "session" not in response.cookies
        finally:
            app.dependency_overrides.clear()


class TestLogout:
    def test_retorna_200_e_remove_cookie(self) -> None:
        client = TestClient(app)
        response = client.post("/api/auth/logout")

        assert response.status_code == 200
        assert response.json() == {"authenticated": False}
