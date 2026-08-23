from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, chat, faq, metrics

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


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
