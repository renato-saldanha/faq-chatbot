from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.chat import get_chat_service
from app.main import app
from app.rate_limit import limiter
from app.services.chat_service import ChatResponse


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    limiter.reset()
    yield
    limiter.reset()


def _override_chat_service(response: ChatResponse) -> AsyncMock:
    service = AsyncMock()
    service.ask.return_value = response
    app.dependency_overrides[get_chat_service] = lambda: service
    return service


def test_ask_com_match_retorna_200_e_resposta() -> None:
    _override_chat_service(
        ChatResponse(
            resposta="Acesse a página de cadastro.",
            faq_item_id=1,
            categoria="Conta",
            sem_resposta=False,
            score=0.95,
        )
    )
    client = TestClient(app)
    response = client.post("/api/chat/ask", json={"pergunta": "Como cadastro uma conta?"})

    assert response.status_code == 200
    body = response.json()
    assert body["resposta"] == "Acesse a página de cadastro."
    assert body["sem_resposta"] is False
    assert body["faq_item_id"] == 1


def test_ask_sem_match_retorna_sem_resposta_true() -> None:
    _override_chat_service(
        ChatResponse(resposta="fallback", faq_item_id=None, categoria=None, sem_resposta=True, score=None)
    )
    client = TestClient(app)
    response = client.post("/api/chat/ask", json={"pergunta": "pergunta sem relação nenhuma"})

    assert response.status_code == 200
    body = response.json()
    assert body["sem_resposta"] is True
    assert body["faq_item_id"] is None


def test_ask_pergunta_vazia_retorna_422() -> None:
    _override_chat_service(
        ChatResponse(resposta="fallback", faq_item_id=None, categoria=None, sem_resposta=True, score=None)
    )
    client = TestClient(app)
    response = client.post("/api/chat/ask", json={"pergunta": "   "})

    assert response.status_code == 422


def test_ask_sem_campo_pergunta_retorna_422() -> None:
    client = TestClient(app)
    response = client.post("/api/chat/ask", json={})

    assert response.status_code == 422


def test_ask_acima_do_limite_retorna_429() -> None:
    _override_chat_service(ChatResponse(resposta="ok", faq_item_id=1, categoria="Conta", sem_resposta=False, score=0.9))
    client = TestClient(app)
    for _ in range(10):
        response = client.post("/api/chat/ask", json={"pergunta": "Como cadastro uma conta?"})
        assert response.status_code == 200

    response = client.post("/api/chat/ask", json={"pergunta": "Como cadastro uma conta?"})

    assert response.status_code == 429
    assert response.json() == {"detail": "Muitas requisições. Tente novamente em instantes."}
