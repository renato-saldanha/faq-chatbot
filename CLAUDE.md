## Projeto

Chatbot de FAQ com Dashboard Analítico — desafio técnico full stack. Chatbot que responde perguntas frequentes consultando uma base de conhecimento cadastrada, com dashboard de métricas de uso (volume, perguntas mais frequentes, taxa de sem-resposta, distribuição por categoria, evolução temporal) e painel admin (CRUD da base, protegido por login OTP).

Requisitos completos: `docs/PRD.md`. Passo a passo de implementação: `docs/PLANO_IMPLEMENTACAO.md`.

## Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.0 (async, `asyncpg`), Alembic, Pydantic v2 (`pydantic-settings`), `rapidfuzz` (similaridade), `pgvector` (schema já preparado para embedding, backend ativo é fuzzy — ver PRD §5), `python-jose` (JWT), `cachetools` (OTP/rate-limit em memória)
- **Banco:** PostgreSQL 16 com extensão `pgvector` (imagem `pgvector/pgvector:pg16`)
- **Frontend:** Next.js 14 (App Router), TypeScript, TanStack Query, Zustand, Recharts, Zod, Vitest — CSS puro em `globals.css` (sem Tailwind/Shadcn neste projeto)
- **Auth do admin:** OTP por e-mail (SMTP via stdlib `smtplib`) + JWT em cookie httpOnly — single-admin via `ADMIN_EMAIL`, sem tabela de usuários (decisão registrada em PRD §9)
- **Conteinerização:** Docker (`docker-compose.yml` na raiz — postgres + backend + frontend)

## Arquitetura

```
Chat público  → POST /api/chat/ask        → ChatService → SimilarityService (fuzzy) → FaqItem
Admin (login) → GET/POST/PUT/DELETE /api/faq/*, /api/metrics/*  → require_admin_session (cookie JWT)
```

Fluxo: `Rota (api/) → Service → Repository → Modelo (SQLAlchemy)`. Cada camada só conhece a de baixo — nunca `api/` acessando modelo direto, nunca repository conhecendo service.

## Estrutura do projeto

```
backend/
├── app/
│   ├── main.py                # FastAPI app + routers + /health
│   ├── config.py               # Settings via pydantic-settings
│   ├── db.py                   # engine async + get_db_session (Depends)
│   ├── models/                 # Categoria, FaqItem, Interacao (SQLAlchemy)
│   ├── api/                    # Rotas — chat.py (público), faq.py/metrics.py (admin), auth.py
│   │   └── _deps.py             # require_admin_session (dependency de proteção)
│   ├── services/                # ChatService, SimilarityService, AuthService — lógica de negócio
│   ├── repositories/             # Acesso a dados: Faq, Interacao, TimeseriesMetrics, FaqMetrics
│   └── auth/                     # otp_store.py, jwt.py — mecanismo de sessão do admin
├── alembic/                     # Migrations (extensão pgvector + 3 tabelas)
├── scripts/seed_faq.py           # Seed idempotente, rodado automaticamente no boot do container
├── tests/                        # Espelha app/ (mocks/fakes, sem depender de Postgres real)
├── entrypoint.sh                 # alembic upgrade head + seed + uvicorn, nessa ordem
└── Dockerfile

frontend/
├── src/app/
│   ├── (chat)/page.tsx           # Chat público, sem login
│   ├── (auth)/login/page.tsx      # Form de e-mail + OTP
│   └── (dashboard)/               # metricas/, faq/ — atrás do guard de sessão
├── src/components/domain/         # chat-window, metric-card, timeseries-chart, category-breakdown-chart, login-form, verify-form
├── src/lib/api.ts                 # Cliente fetch fino, credentials:include
├── src/stores/auth-store.ts       # Zustand — estado de sessão do lado UI (fonte de verdade real é o cookie httpOnly)
└── src/types/api.ts               # Contrato TS espelhando os schemas Pydantic do backend — única fonte de shape de request/response

docker-compose.yml   # postgres (pgvector) + backend + frontend
.env.example          # Todas as vars — nunca commitar .env com valor real
```

## Convenções de código (backend Python)

- **Naming:** domínio em português (`Categoria`, `FaqItem`, `Interacao`, `pergunta`, `resposta`, `sem_resposta`) — é o vocabulário do próprio PRD/enunciado do desafio. Nomes de função/parâmetro técnicos (`get_db_session`, `session`, `repo`) em inglês. `snake_case` em Python, `PascalCase` em classes.
- **Async:** toda rota e método de repository/service que toca I/O é `async def`. Type hints obrigatórios, `X | None` (não `Optional[X]`).
- **Imports:** absolutos a partir de `app.` (nunca relativo `from ..`). Ordem stdlib → third-party → local — `ruff` organiza (`ruff check --fix`).
- **Pydantic vs dataclass:** `BaseModel` para I/O de API (request/response); `@dataclass(frozen=True)` para estrutura interna imutável entre camadas (`MatchResult`, `MetricsSummary`, `DailyCount`, etc — nunca vazam pro Pydantic de resposta diretamente, a rota faz a conversão explícita).
- **Injeção de dependência sempre.** Nenhuma classe instancia sua própria dependência (`self.x = AlgumaCoisa()` proibido). Repository recebe `AsyncSession` via `__init__`; service recebe repository(s)/outros services via `__init__`; rota resolve tudo via `Depends()`. Exceções: primitivos stdlib sem estado (`datetime.now()`, `secrets.randbelow()`).
- **Forward reference em `relationship()`:** usar `TYPE_CHECKING` + import real, nunca `# noqa: F821` sozinho — mypy precisa enxergar o tipo (ver `app/models/categoria.py`/`faq_item.py`).
- **`SimilarityService` é a única fronteira de "quão parecida é uma pergunta".** Nenhum código fora de `services/similarity_service.py` lê `embedding`/compara texto diretamente — tudo passa por `find_best_match`/`vector_for`. Isso existe para permitir trocar o backend (fuzzy → embedding, se um dia for implementado) sem tocar em `ChatService` nem em quem consome métricas.
- **Segredos:** `JWT_SECRET_KEY`, `SMTP_PASSWORD`, `OPENAI_API_KEY` só via `Settings`/env var — nunca hardcoded, nunca logados.
- **Testes:** pytest + pytest-asyncio, `tests/` espelha `app/`. Repository testado com `AsyncMock`/`MagicMock` na sessão (sem Postgres real rodando) — assert no que foi chamado (`session.add`, `session.execute` com a query certa), não no resultado de uma query real. Um assert por conceito.

## Convenções de código (frontend)

- Componentes de página em `src/app/**/page.tsx`; componentes reutilizáveis em `src/components/domain/`.
- Todo componente com hook (`useState`, `useQuery`, etc.) tem `"use client"` no topo.
- Tipos de API sempre de `src/types/api.ts` — nunca redefinir um shape equivalente solto num componente.
- Mutations (`useMutation`) que alteram dado devem invalidar a query relevante via `queryClient.invalidateQueries` — CRUD precisa refletir na lista sem F5.
- Gráficos (Recharts) precisam renderizar sem quebrar com array vazio — mostrar estado "sem dados", não deixar o componente estourar.

## Comandos

```bash
# Setup local (sem Docker)
cd backend && pip install -r requirements.txt
cp ../.env.example ../.env   # editar valores reais
alembic upgrade head
python -m scripts.seed_faq
uvicorn app.main:app --reload --port 8000

cd frontend && npm install
npm run dev

# Docker (recomendado — sobe os 3 serviços, migration+seed automáticos)
docker compose up --build

# Testes/lint backend
cd backend
pytest tests/ -v
ruff check . && ruff format --check .
mypy app/

# Testes/lint frontend
cd frontend
npm run test
npm run lint
npx tsc --noEmit

# Migrations
cd backend
alembic revision --autogenerate -m "descrição"
alembic upgrade head
```

## Decisões de escopo (corte sob prazo — ver histórico de commits)

- **`SIMILARITY_BACKEND=fuzzy` único implementado.** PRD §5 previa 3 protótipos (fuzzy/embedding/híbrido) com script de avaliação comparativo — cortado por restrição de tempo. Schema já suporta `embedding` (coluna `pgvector` em `FaqItem`/`Interacao`), a interface `SimilarityService` já é abstrata o bastante para adicionar um segundo backend depois sem quebrar `ChatService`.
- **CI/CD (GitHub Actions + gate de review por IA) foi configurado e depois desativado** sob a mesma restrição de tempo — branch protection removida, trabalho commitado direto na branch principal. Os workflows (`.github/workflows/`) continuam no repositório como referência, mas não estão ativos/obrigatórios.
- **Sem testes E2E** (Playwright/Cypress) — fora do escopo dado o prazo; cobertura é unitária (backend) e ausente no momento (frontend, ver `PLANO_IMPLEMENTACAO.md` Parte 9, não priorizada).

## Documentação

- `docs/PRD.md` — requisitos mapeados linha a linha do enunciado (C1-C5 chatbot, D1-D6 dashboard), decisões técnicas, modelo de dados, arquitetura.
- `docs/PLANO_IMPLEMENTACAO.md` — plano original em 12 Partes (nem todas completadas — ver seção de decisões de escopo acima).
