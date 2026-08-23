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
Chat público  → POST /api/chat/ask        → ChatService → SimilarityService (fuzzy|embedding|hybrid) → FaqItem
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
- **`SimilarityService` é a única fronteira de "quão parecida é uma pergunta".** Nenhum código fora de `services/similarity_service.py` lê `embedding`/compara texto diretamente — tudo passa por `find_best_match`/`vector_for`. Três implementações (`FuzzySimilarityService`, `EmbeddingSimilarityService`, `HybridSimilarityService`) selecionáveis via `SIMILARITY_BACKEND`, sem tocar em `ChatService` nem em quem consome métricas.
- **Segredos:** `JWT_SECRET_KEY`, `SMTP_PASSWORD`, `OPENAI_API_KEY` só via `Settings`/env var — nunca hardcoded, nunca logados.
- **Testes:** pytest + pytest-asyncio, `tests/` espelha `app/`. Repository testado com `AsyncMock`/`MagicMock` na sessão (sem Postgres real rodando) — assert no que foi chamado (`session.add`, `session.execute` com a query certa), não no resultado de uma query real. Um assert por conceito.

## Convenções de código (frontend)

- Componentes de página em `src/app/**/page.tsx`; componentes reutilizáveis em `src/components/domain/`.
- Todo componente com hook (`useState`, `useQuery`, etc.) tem `"use client"` no topo.
- Tipos de API sempre de `src/types/api.ts` — nunca redefinir um shape equivalente solto num componente.
- Mutations (`useMutation`) que alteram dado devem invalidar a query relevante via `queryClient.invalidateQueries` — CRUD precisa refletir na lista sem F5.
- Gráficos (Recharts) precisam renderizar sem quebrar com array vazio — mostrar estado "sem dados", não deixar o componente estourar. Cores dos gráficos (`stroke`/`fill`) usam CSS variables (`var(--primary)`, `var(--border)` etc — Recharts aceita string CSS normal), nunca hex fixo, para reagir a dark mode automaticamente sem duplicar lógica de tema em JS.
- **Ações em linha de tabela (ex: "Editar"/"Excluir" em `.data-table`) sempre alinhadas na horizontal, nunca empilhadas verticalmente.** A célula de ações usa a classe `actions-cell` (`display: flex; flex-direction: row; gap` no CSS) — nunca depender do wrap natural de botões inline, que quebra linha silenciosamente quando o espaço aperta.
- **Tema claro/escuro é obrigatório em toda tela nova.** Todo token de cor vem de CSS variables em `:root` (light) + `@media (prefers-color-scheme: dark)` guardado por `:not([data-theme="light"])` + `:root[data-theme="dark"]` (mesmo padrão de 3 blocos usado em Artifacts) — nunca hardcodar hex direto num componente ou classe fora desses blocos. O toggle (`src/components/ui/theme-toggle.tsx`) grava a escolha em `localStorage` e aplica via atributo `data-theme` no `<html>`; o script inline em `layout.tsx` lê esse valor antes da hidratação para evitar flash de tema errado.
- **Telas do chat público (`/`) são para o usuário final, que pode não ter instrução técnica — a experiência precisa ser fluida sem exigir familiaridade com jargão de sistema.** Ao escrever ou revisar UI dessa área: erros de rede/API não podem ficar só num toast passageiro — o estado de falha precisa ficar visível no próprio elemento afetado (ex: a bolha da pergunta que falhou), porque quem não é técnico não necessariamente associa um toast a "minha última ação falhou". Telas vazias sem contexto (`"Faça uma pergunta para começar"` sozinho) não ajudam quem não sabe o que o sistema cobre — dar exemplos/sugestões de ação como ponto de partida. Qualquer navegação para a área administrativa (`/login`) deve usar linguagem que fale com quem trabalha ali ("Painel interno"), nunca termos de sistema como "admin"/"dashboard"/"OTP" expostos ao usuário final — e ficar visualmente separada do fluxo principal (ex: botão no canto, não misturado ao conteúdo do chat). O painel admin (`/faq`, `/metricas`), por outro lado, pode usar linguagem mais técnica — é usado por quem opera o sistema, não pelo cliente final.

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

## Regras de processo

- **Nunca confiar no relatório de um subagent como prova de que o código existe/funciona.** Sempre confirmar com `ls`/`Read` o arquivo real e rodar o comando de teste/lint você mesmo antes de aceitar como concluído.
- **Nunca dar `git add <diretório>` genérico esperando pegar só uma mudança.** Ele pega TODO o conteúdo pendente daquele diretório. Sempre `git status --short` antes de `git add`, e usar `git add <arquivo específico>` quando a intenção é isolar uma mudança.
- **Código gerado por agente em paralelo entra como "não verificado" até `install`/`build`/`typecheck`/testes rodarem até o fim, sem erro, na sua própria execução.** Escrever o código não é o mesmo que validá-lo.
- **`npm install`/`tsc`/`lint` limpos não substituem `docker compose up --build`.** `next build` roda pré-renderização estática (SSG) que `tsc --noEmit` não executa — um bug de rota (ex: colisão de rota entre `app/page.tsx` e um route group `(grupo)/page.tsx` mapeando pro mesmo path) só aparece no build de verdade. Rodar o smoke test via Docker antes de considerar o frontend pronto para entrega.
- **Smoke test / teste manual de frontend sempre via Playwright em modo headless**, nunca a extensão Claude in Chrome (não confiável neste ambiente — já falhou por desconexão) nem screenshot manual pedindo pro usuário navegar. Instalar como dependência do projeto (`npm install -D @playwright/test && npx playwright install --with-deps chromium`) em vez de `npx playwright` avulso, e escrever o script de smoke test contra `http://localhost:3000` (stack já de pé via `docker compose up`) com `headless: true` explícito.
- **PR novo = worktree nova.** Ao começar uma frente de trabalho distinta que vai virar seu próprio PR (nova feature, fix não relacionado ao que já está em andamento), criar uma worktree git nova (`git worktree add` ou `EnterWorktree`) em vez de continuar na mesma worktree/branch já em uso — nunca misturar mudanças de propósitos diferentes no mesmo diretório de trabalho. Não se aplica a commits sequenciais dentro da mesma unidade de trabalho, só a frentes novas e independentes.

## Docker neste ambiente (Windows)

- **Se `docker`/`docker compose` não forem reconhecidos no PATH da sessão atual do shell** (comum logo após instalar o Docker Desktop, ou quando ele foi instalado em local não padrão), localizar o binário com `Get-ChildItem -Recurse -Filter docker.exe` a partir da pasta de instalação real do Docker Desktop (neste ambiente: `C:\Users\renat\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe` — **não** o caminho padrão `C:\Program Files\Docker`). Adicionar essa pasta ao `$env:PATH` da sessão PowerShell antes de rodar `docker`/`docker compose`.
- **Verificar se o Docker Desktop está de fato pronto** com `docker ps` antes de rodar `docker compose up` — processos `Docker Desktop`/`com.docker.backend` ativos no Task Manager não significam que o daemon já aceita comandos.
- **Sempre garantir `.dockerignore` em qualquer diretório com `node_modules`/`.git` antes do primeiro `docker compose up --build`.** Sem ele, o build envia esse conteúdo inteiro como contexto (aqui chegou a ~350MB e travou a transferência por minutos) mesmo com Dockerfile multi-stage — o `COPY . .` do estágio de build reenvia tudo que está no contexto, independente do que foi copiado nos estágios anteriores.
- **Se um build travar visivelmente sem progredir** (ex: `transferring context` crescendo devagar por mais de ~1 min), considerar `docker compose down` + corrigir a causa (geralmente `.dockerignore` ausente) + subir de novo, em vez de esperar — mais rápido sob prazo apertado do que deixar terminar.
- **Rodar `docker compose up --build` em background (`run_in_background`)** e monitorar via `Monitor` com polling em `curl` nos health checks (`http://localhost:8000/health`, `http://localhost:3000`) — evita ficar bloqueado esperando o build inteiro para descobrir se algo quebrou.

## Decisões de escopo (ver histórico de commits)

- **PRD §5 — 3 protótipos de similaridade (fuzzy/embedding/híbrido) implementados**, selecionáveis via `SIMILARITY_BACKEND`. Gabarito de avaliação (`scripts/similarity_eval_dataset.json` + `scripts/eval_similarity.py`) roda contra qualquer backend ativo — resultado documentado no README.
- **CI/CD ativo** (`.github/workflows/ci.yml`) — lint/typecheck/test de backend e frontend + build do Docker Compose, em todo push/PR. Sem branch protection configurada, então o merge continua manual mesmo com gates rodando.
- **Sem testes E2E automatizados em CI** (Playwright/Cypress) — cobertura é unitária (backend, 30 testes) e de componente (frontend, 29 testes via Vitest); smoke test manual via Playwright headless é usado ad-hoc em validação, não como suíte no CI.

## Documentação

- `docs/PRD.md` — requisitos mapeados linha a linha do enunciado (C1-C5 chatbot, D1-D6 dashboard), decisões técnicas, modelo de dados, arquitetura.
- `docs/PLANO_IMPLEMENTACAO.md` — plano original em 12 Partes (nem todas completadas — ver seção de decisões de escopo acima).
