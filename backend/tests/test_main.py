from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import unhandled_exception_handler


def _make_app_with_broken_route() -> FastAPI:
    app = FastAPI()
    app.add_exception_handler(Exception, unhandled_exception_handler)

    @app.get("/boom")
    async def boom() -> None:
        raise RuntimeError("falha inesperada")

    return app


def test_excecao_nao_tratada_retorna_500_com_detail_generico() -> None:
    client = TestClient(_make_app_with_broken_route(), raise_server_exceptions=False)

    response = client.get("/boom")

    assert response.status_code == 500
    assert response.json() == {"detail": "Erro interno do servidor."}
