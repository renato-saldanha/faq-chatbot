import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import auth, chat, faq, metrics

logger = logging.getLogger(__name__)

app = FastAPI(title="Chatbot de FAQ com Dashboard Analítico")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(faq.router)
app.include_router(metrics.router)
app.include_router(auth.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Rede de segurança para erro não previsto (ex.: falha de conexão com o banco).

    Rotas já tratam seus erros esperados via HTTPException (404/401/422) — este
    handler só cobre o que sobra, para nunca vazar traceback/detalhe interno ao
    cliente e sempre responder no mesmo formato {"detail": ...} do FastAPI.
    """
    logger.exception("Erro não tratado em %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Erro interno do servidor."})


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
