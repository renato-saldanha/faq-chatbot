# Chatbot de FAQ com Dashboard Analítico

Desafio técnico full stack: chatbot que responde perguntas frequentes consultando uma base de conhecimento cadastrada, com dashboard de métricas de uso e painel admin (CRUD da base, protegido por login OTP).

Requisitos completos: `docs/PRD.md`. Plano de implementação original: `docs/PLANO_IMPLEMENTACAO.md`.

## Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.0 (async, `asyncpg`), Alembic, Pydantic v2, `rapidfuzz` (similaridade), `pgvector`, `python-jose` (JWT)
- **Banco:** PostgreSQL 16 com extensão `pgvector`
- **Frontend:** Next.js 14 (App Router), TypeScript, TanStack Query, Zustand, Recharts, Zod
- **Auth do admin:** OTP por e-mail + JWT em cookie httpOnly — single-admin via `ADMIN_EMAIL`
- **Conteinerização:** Docker (`docker-compose.yml` na raiz — postgres + backend + frontend)

## Como rodar

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000 (docs em `/docs`)

No primeiro boot, o container do backend roda `alembic upgrade head` e depois o seed de FAQ (`scripts/seed_faq.py`, idempotente) automaticamente — não é preciso nenhum passo manual de setup de banco.

Para resetar o banco do zero (testar o bootstrap novamente):

```bash
docker compose down -v   # remove o volume do Postgres
docker compose up --build
```

### Login admin (OTP)

Sem `SMTP_HOST` configurado (padrão do `.env.example`), o código OTP não é enviado por e-mail de verdade — ele é logado no console do container `backend`:

```bash
docker compose logs -f backend
```

Procure pela linha `SMTP não configurado — OTP para <email>: <código>` (ver `AuthService._send_email`). Para enviar e-mails reais, preencha `SMTP_HOST`/`SMTP_USER`/`SMTP_PASSWORD` no `.env`.

### Smoke test manual

A base fictícia (`scripts/seed_faq.py`) já popula 50 perguntas em 6 categorias no primeiro boot — não é preciso cadastrar nada manualmente para testar o fluxo completo:

1. Suba a stack (`docker compose up --build`) e abra http://localhost:3000 — o chat já responde perguntas do seed (ex: "Como recupero minha senha?") e trata pergunta sem match retornando `sem_resposta: true`.
2. Clique em "Painel interno" (canto superior direito do chat) → login com o `ADMIN_EMAIL` configurado → código OTP (log do backend ou e-mail real, conforme SMTP) → cai direto na tela de FAQ.
3. Teste o CRUD: criar uma pergunta nova, verificar que ela já aparece na lista e responde no chat sem precisar reiniciar nada; editar e excluir também refletem imediatamente. Em "Métricas" (nav do topo), as interações do passo 1 já aparecem nos gráficos e cards.
4. Para repetir o teste do zero (base limpa, sem histórico de interações): `docker compose down -v && docker compose up --build` — a migration (`alembic upgrade head`) recria o schema e o seed repovoa a base fictícia automaticamente, sem passo manual algum.

## Variáveis de ambiente

Todas em `.env.example`:

| Variável | Descrição |
|---|---|
| `DATABASE_URL` | String de conexão async do Postgres (já resolvida para o serviço `postgres` do Compose) |
| `SIMILARITY_BACKEND` | Backend de similaridade ativo — `fuzzy` (único implementado, ver decisão abaixo) |
| `SIMILARITY_THRESHOLD` | Limiar mínimo de score (0–1) para considerar um match válido |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | Reservado para um backend de similaridade por embedding (não implementado — ver abaixo) |
| `ADMIN_EMAIL` | E-mail autorizado a logar no painel admin (single-admin, sem tabela de usuários) |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` | Envio do código OTP por e-mail; vazio = OTP cai no log do backend (ver acima) |
| `JWT_SECRET_KEY` | Segredo de assinatura do JWT de sessão do admin — trocar em produção |

## Decisão: similaridade por fuzzy matching

O PRD original (`docs/PRD.md` §5) previa comparar três protótipos — léxico/fuzzy, semântico via embedding OpenAI, e um híbrido — com um gabarito de perguntas e métricas de acurácia/latência antes de escolher o backend definitivo.

**O protótipo A (fuzzy, via `rapidfuzz`) foi o escolhido e implementado**; os protótipos B (embedding) e C (híbrido) e o script de avaliação comparativo ficaram fora do escopo desta entrega — decisão de escopo, não lacuna técnica:

- Fuzzy matching é determinístico, sem custo/dependência de API externa, e cobre bem o caso mais comum do desafio (perguntas próximas ao texto da FAQ, com ou sem erro de digitação).
- O ponto fraco conhecido é paráfrase com vocabulário muito diferente ("como cancelo minha conta" vs "quero encerrar meu cadastro") — nesse caso, o chatbot retorna sem-resposta em vez de um match forçado.
- O schema já foi desenhado para suportar a extensão: `FaqItem` e `Interacao` têm coluna `embedding` (`pgvector`), e `SimilarityService` é a única fronteira de "quão parecida é uma pergunta" no código — nenhum outro módulo lê `embedding` ou compara texto diretamente. Adicionar um backend de embedding depois não deveria exigir tocar em `ChatService` nem em quem consome métricas.

## Estrutura do projeto

```
backend/
├── app/
│   ├── main.py                # FastAPI app + routers + /health
│   ├── config.py               # Settings via pydantic-settings
│   ├── db.py                   # engine async + get_db_session
│   ├── models/                 # Categoria, FaqItem, Interacao (SQLAlchemy)
│   ├── api/                    # Rotas — chat.py (público), faq.py/metrics.py (admin), auth.py
│   ├── services/                # ChatService, SimilarityService, AuthService
│   ├── repositories/             # Acesso a dados
│   └── auth/                     # otp_store.py, jwt.py
├── alembic/                     # Migrations (extensão pgvector + 3 tabelas)
├── scripts/seed_faq.py           # Seed idempotente, rodado automaticamente no boot
├── tests/                        # 30 testes, espelha app/, sem depender de Postgres real
└── Dockerfile

frontend/
├── src/app/
│   ├── (chat)/page.tsx           # Chat público, sem login
│   ├── (auth)/login/page.tsx      # Form de e-mail + OTP
│   └── (dashboard)/               # metricas/, faq/ — atrás do guard de sessão
├── src/components/domain/         # chat-window, metric-card, timeseries-chart, category-breakdown-chart, login-form, verify-form
├── src/lib/api.ts                 # Cliente fetch fino, credentials:include
├── src/stores/auth-store.ts       # Zustand — estado de sessão do lado UI
└── src/types/api.ts               # Contrato TS espelhando os schemas Pydantic do backend

docker-compose.yml   # postgres (pgvector) + backend + frontend
.env.example          # Todas as vars — nunca commitar .env com valor real
```

Detalhes de arquitetura e convenções de código: `CLAUDE.md` na raiz.

## Padrões de arquitetura

**Backend**

- **Camadas em cadeia unidirecional:** `api/` (rota FastAPI) → `services/` (regra de negócio) → `repositories/` (acesso a dados) → `models/` (SQLAlchemy). Cada camada só conhece a de baixo — nenhuma rota acessa modelo direto, nenhum repository conhece service.
- **Repository Pattern** (`app/repositories/`) — cada repository (`FaqRepository`, `InteracaoRepository`, `TimeseriesMetricsRepository`, `FaqMetricsRepository`) isola toda a query SQLAlchemy da tabela correspondente; services nunca montam `select(...)` diretamente.
- **Strategy Pattern** (`app/services/similarity_service.py`) — `SimilarityService` é uma interface abstrata (`find_best_match`, `vector_for`); `FuzzySimilarityService` é a única implementação hoje, mas o `ChatService` e o restante do código dependem só da interface, nunca da classe concreta — trocar o backend de similaridade (ex: por embedding) não exige tocar em quem consome.
- **Dependency Injection via constructor + FastAPI `Depends()`:** nenhuma classe instancia sua própria dependência (`self.x = AlgumaCoisa()` é proibido pela convenção do projeto). Repository recebe `AsyncSession` no `__init__`; service recebe repository(s)/outros services no `__init__`; a rota resolve a árvore inteira via `Depends(get_chat_service)` (ver `app/api/chat.py`). Isso é o que torna os services testáveis com fakes, sem subir Postgres real nos testes.
- **DTO explícito entre camadas:** `MatchResult`, `ChatResponse`, `MetricsSummary` são `@dataclass(frozen=True)` — estruturas imutáveis internas que nunca vazam para o Pydantic de resposta HTTP sem conversão explícita na rota. Pydantic (`BaseModel`) fica reservado para I/O de API (validação de request/response).

**Frontend**

- **Container/presentational implícito via App Router:** páginas (`src/app/**/page.tsx`) orquestram data-fetching (`useQuery`/`useMutation`) e passam dados prontos para componentes de domínio (`src/components/domain/`), que são majoritariamente apresentacionais.
- **Client fino centralizado** (`src/lib/api.ts`) — único ponto que fala com o backend; nenhum componente chama `fetch` diretamente, o que mantém `credentials: "include"` e o tratamento de erro consistentes em um lugar.
- **Store global mínimo** (`src/stores/auth-store.ts`, Zustand) — só o essencial de estado de sessão do lado UI; a fonte de verdade real da sessão é o cookie JWT httpOnly, a store existe para o guard de rota decidir renderizar sem esperar um round-trip.
- **Contrato de tipos compartilhado** (`src/types/api.ts`) — espelha os schemas Pydantic do backend; nunca um componente redefine um shape equivalente solto.
- **Design tokens via CSS variables** (`src/app/globals.css`) — toda cor/espaçamento vem de `var(--token)`, nunca hex direto num componente; permite alternar tema claro/escuro (`data-theme` no `<html>`) sem duplicar lógica de estilo em JS.

## Testes e lint

```bash
# Backend
cd backend
pytest tests/ -v          # 30 passed
ruff check . && mypy app/  # ambos limpos

# Frontend
cd frontend
npx tsc --noEmit
npm run lint
npm run test          # 29 passed
```

## Fora do escopo desta entrega (decisões conscientes)

- **`SIMILARITY_BACKEND=fuzzy` único** — ver seção de decisão acima.
- **CI/CD desativado.** Foi construído (GitHub Actions com gate de review por IA) e depois desativado. Os arquivos `.github/workflows/*.yml` continuam no repositório como referência, mas não estão ativos — branch protection foi removida, trabalho commitado direto na branch principal.
- **Sem testes E2E** (Playwright/Cypress).
