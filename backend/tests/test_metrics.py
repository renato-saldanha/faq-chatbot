from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from app.api._deps import require_admin_session
from app.api.metrics import (
    get_faq_metrics_repository,
    get_interacao_repository,
    get_timeseries_metrics_repository,
)
from app.main import app


def _override_auth() -> None:
    app.dependency_overrides[require_admin_session] = lambda: "admin@example.com"


class TestMetricsRoutesAuth:
    def test_summary_sem_sessao_retorna_401(self) -> None:
        client = TestClient(app)
        response = client.get("/api/metrics/summary")

        assert response.status_code == 401


class TestGetSummary:
    def test_retorna_summary_serializado(self) -> None:
        _override_auth()
        repo = AsyncMock()
        summary = MagicMock()
        summary.total_conversas = 10
        summary.total_sem_resposta = 2
        summary.taxa_sem_resposta = 0.2
        repo.get_summary.return_value = summary
        app.dependency_overrides[get_timeseries_metrics_repository] = lambda: repo
        client = TestClient(app)
        response = client.get("/api/metrics/summary")

        assert response.status_code == 200
        assert response.json() == {
            "total_conversas": 10,
            "total_sem_resposta": 2,
            "taxa_sem_resposta": 0.2,
        }


class TestGetTimeseries:
    def test_retorna_serie_diaria(self) -> None:
        _override_auth()
        repo = AsyncMock()
        daily = MagicMock()
        daily.data = "2026-08-01"
        daily.quantidade = 5
        repo.get_daily_series.return_value = [daily]
        app.dependency_overrides[get_timeseries_metrics_repository] = lambda: repo
        client = TestClient(app)
        response = client.get("/api/metrics/timeseries")

        assert response.status_code == 200
        assert response.json() == [{"data": "2026-08-01", "quantidade": 5}]


class TestGetTopQuestions:
    def test_retorna_top_questions(self) -> None:
        _override_auth()
        repo = AsyncMock()
        top = MagicMock()
        top.faq_item_id = 1
        top.pergunta = "Como cadastro?"
        top.quantidade = 8
        repo.get_top_questions.return_value = [top]
        app.dependency_overrides[get_faq_metrics_repository] = lambda: repo
        client = TestClient(app)
        response = client.get("/api/metrics/top-questions")

        assert response.status_code == 200
        assert response.json() == [{"faq_item_id": 1, "pergunta": "Como cadastro?", "quantidade": 8}]


class TestGetCategories:
    def test_retorna_breakdown_por_categoria(self) -> None:
        _override_auth()
        repo = AsyncMock()
        breakdown = MagicMock()
        breakdown.categoria = "Conta"
        breakdown.quantidade = 4
        repo.get_category_breakdown.return_value = [breakdown]
        app.dependency_overrides[get_faq_metrics_repository] = lambda: repo
        client = TestClient(app)
        response = client.get("/api/metrics/categories")

        assert response.status_code == 200
        assert response.json() == [{"categoria": "Conta", "quantidade": 4}]


class TestGetUnanswered:
    def test_retorna_perguntas_sem_resposta(self) -> None:
        _override_auth()
        repo = AsyncMock()
        interacao = MagicMock()
        interacao.id = 1
        interacao.pergunta_usuario = "pergunta esquisita"
        interacao.criado_em.isoformat.return_value = "2026-08-01T10:00:00"
        repo.get_unanswered.return_value = [interacao]
        app.dependency_overrides[get_interacao_repository] = lambda: repo
        client = TestClient(app)
        response = client.get("/api/metrics/unanswered")

        assert response.status_code == 200
        assert response.json() == [
            {"id": 1, "pergunta_usuario": "pergunta esquisita", "criado_em": "2026-08-01T10:00:00"}
        ]
