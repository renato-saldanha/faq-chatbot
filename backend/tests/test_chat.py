from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.api.chat import get_chat_service
from app.main import app
from app.services.chat_service import ChatResponse


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
    try:
        client = TestClient(app)
        response = client.post("/api/chat/ask", json={"pergunta": "Como cadastro uma conta?"})

        assert response.status_code == 200
        body = response.json()
        assert body["resposta"] == "Acesse a página de cadastro."
        assert body["sem_resposta"] is False
        assert body["faq_item_id"] == 1
    finally:
        app.dependency_overrides.clear()


def test_ask_sem_match_retorna_sem_resposta_true() -> None:
    _override_chat_service(
        ChatResponse(resposta="fallback", faq_item_id=None, categoria=None, sem_resposta=True, score=None)
    )
    try:
        client = TestClient(app)
        response = client.post("/api/chat/ask", json={"pergunta": "pergunta sem relação nenhuma"})

        assert response.status_code == 200
        body = response.json()
        assert body["sem_resposta"] is True
        assert body["faq_item_id"] is None
    finally:
        app.dependency_overrides.clear()


def test_ask_pergunta_vazia_retorna_422() -> None:
    _override_chat_service(
        ChatResponse(resposta="fallback", faq_item_id=None, categoria=None, sem_resposta=True, score=None)
    )
    try:
        client = TestClient(app)
        response = client.post("/api/chat/ask", json={"pergunta": "   "})

        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_ask_sem_campo_pergunta_retorna_422() -> None:
    client = TestClient(app)
    response = client.post("/api/chat/ask", json={})

    assert response.status_code == 422
