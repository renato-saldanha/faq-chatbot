from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from app.api._deps import get_faq_repository, require_admin_session
from app.main import app


def _make_faq_item(id_: int, categoria_id: int, pergunta: str, resposta: str, ativo: bool, categoria_nome: str):
    item = MagicMock()
    item.id = id_
    item.categoria_id = categoria_id
    item.pergunta = pergunta
    item.resposta = resposta
    item.ativo = ativo
    item.categoria = MagicMock()
    item.categoria.nome = categoria_nome
    return item


def _override_repo() -> AsyncMock:
    repo = AsyncMock()
    app.dependency_overrides[get_faq_repository] = lambda: repo
    app.dependency_overrides[require_admin_session] = lambda: "admin@example.com"
    return repo


class TestFaqRoutesAuth:
    def test_list_faq_sem_sessao_retorna_401(self) -> None:
        client = TestClient(app)
        response = client.get("/api/faq")

        assert response.status_code == 401


class TestListFaq:
    def test_retorna_lista_serializada(self) -> None:
        repo = _override_repo()
        repo.list_all.return_value = [
            _make_faq_item(1, 2, "Como cadastro?", "Acesse o site.", True, "Conta"),
        ]
        try:
            client = TestClient(app)
            response = client.get("/api/faq")

            assert response.status_code == 200
            body = response.json()
            assert body == [
                {
                    "id": 1,
                    "categoria_id": 2,
                    "categoria_nome": "Conta",
                    "pergunta": "Como cadastro?",
                    "resposta": "Acesse o site.",
                    "ativo": True,
                }
            ]
            repo.list_all.assert_awaited_once_with(only_active=False)
        finally:
            app.dependency_overrides.clear()


class TestCreateFaq:
    def test_cria_e_retorna_200(self) -> None:
        repo = _override_repo()
        repo.create.return_value = _make_faq_item(1, 2, "Como cadastro?", "Acesse o site.", True, "Conta")
        try:
            client = TestClient(app)
            response = client.post(
                "/api/faq",
                json={"categoria_id": 2, "pergunta": "Como cadastro?", "resposta": "Acesse o site.", "ativo": True},
            )

            assert response.status_code == 200
            assert response.json()["id"] == 1
            repo.create.assert_awaited_once_with(2, "Como cadastro?", "Acesse o site.")
        finally:
            app.dependency_overrides.clear()

    def test_payload_invalido_retorna_422(self) -> None:
        _override_repo()
        try:
            client = TestClient(app)
            response = client.post("/api/faq", json={"pergunta": "sem categoria_id nem resposta"})

            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()


class TestUpdateFaq:
    def test_atualiza_existente_retorna_200(self) -> None:
        repo = _override_repo()
        repo.update.return_value = _make_faq_item(1, 2, "Nova pergunta?", "Nova resposta.", True, "Conta")
        try:
            client = TestClient(app)
            response = client.put(
                "/api/faq/1",
                json={"categoria_id": 2, "pergunta": "Nova pergunta?", "resposta": "Nova resposta.", "ativo": True},
            )

            assert response.status_code == 200
            assert response.json()["pergunta"] == "Nova pergunta?"
        finally:
            app.dependency_overrides.clear()

    def test_inexistente_retorna_404(self) -> None:
        repo = _override_repo()
        repo.update.return_value = None
        try:
            client = TestClient(app)
            response = client.put(
                "/api/faq/999",
                json={"categoria_id": 2, "pergunta": "p", "resposta": "r", "ativo": True},
            )

            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()


class TestDeleteFaq:
    def test_existente_retorna_200(self) -> None:
        repo = _override_repo()
        repo.delete.return_value = True
        try:
            client = TestClient(app)
            response = client.delete("/api/faq/1")

            assert response.status_code == 200
            assert response.json() == {"deleted": True}
        finally:
            app.dependency_overrides.clear()

    def test_inexistente_retorna_404(self) -> None:
        repo = _override_repo()
        repo.delete.return_value = False
        try:
            client = TestClient(app)
            response = client.delete("/api/faq/999")

            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()


class TestCategorias:
    def test_list_categorias_retorna_200(self) -> None:
        repo = _override_repo()
        categoria = MagicMock()
        categoria.id = 1
        categoria.nome = "Conta"
        categoria.slug = "conta"
        repo.list_categorias.return_value = [categoria]
        try:
            client = TestClient(app)
            response = client.get("/api/faq/categorias")

            assert response.status_code == 200
            assert response.json() == [{"id": 1, "nome": "Conta", "slug": "conta"}]
        finally:
            app.dependency_overrides.clear()

    def test_create_categoria_retorna_200(self) -> None:
        repo = _override_repo()
        categoria = MagicMock()
        categoria.id = 1
        categoria.nome = "Conta"
        categoria.slug = "conta"
        repo.create_categoria.return_value = categoria
        try:
            client = TestClient(app)
            response = client.post("/api/faq/categorias", json={"nome": "Conta", "slug": "conta"})

            assert response.status_code == 200
            repo.create_categoria.assert_awaited_once_with("Conta", "conta")
        finally:
            app.dependency_overrides.clear()
