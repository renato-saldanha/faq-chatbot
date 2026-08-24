# Plano de Implementação — Chatbot de FAQ com Dashboard Analítico

Referência: `PRD.md`. Cada parte é entregável e testável isoladamente antes de avançar para a próxima.

## Parte 0 — Scaffolding e infraestrutura
- Estrutura de pastas `backend/` e `frontend/` criadas do zero (`create-next-app` para o frontend, layout de pacote padrão para o backend FastAPI).
- `docker-compose.yml`: serviço `postgres`, `backend` (FastAPI + uvicorn), `frontend` (Next.js).
- `backend/config.py` via pydantic-settings: `DATABASE_URL`, `OPENAI_API_KEY`, `OPENAI_MODEL`, `SIMILARITY_BACKEND` (`fuzzy` | `embedding` | `hybrid`), `SIMILARITY_THRESHOLD`, `ADMIN_EMAIL`, `SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/`SMTP_PASSWORD`, `JWT_SECRET_KEY`.
- `.env.example` com todas as variáveis, sem valores reais.
- Entrypoint do container `backend` roda `alembic upgrade head` seguido do seed idempotente (`scripts/seed_faq.py` — só popula se `faq_item` estiver vazia) antes de subir o `uvicorn`, para `docker compose up` deixar a aplicação usável sem passo manual (script real só existe a partir das Partes 1/2, mas o entrypoint já é escrito aqui para não virar retrabalho depois).
- Portabilidade Windows/Mac/Ubuntu: imagens base multi-arquitetura (`python:3.11-slim`, `node:20-alpine`, `postgres:16`), sem paths absolutos do host nos volumes (`./backend:/app`), `.gitattributes` forçando `eol=lf` em `*.sh`/`Dockerfile`/scripts de entrypoint para não quebrar shebang por CRLF vindo do Windows.
- Critério de saída: `docker compose up` sobe os 3 serviços, backend responde em `/health`, frontend carrega página em branco — validado localmente (Windows) e a validação cruzada em outro SO fica registrada no README como instrução, já que não há máquina Mac/Ubuntu disponível para testar diretamente neste ambiente.

## Parte 1 — Modelo de dados e base de conhecimento (backend)
- SQLAlchemy models: `Categoria`, `FaqItem`, `Interacao` (schema em PRD §6).
- Alembic: migration inicial.
- `FaqRepository`: CRUD de `FaqItem`/`Categoria`.
- `api/faq.py`: endpoints REST CRUD (`GET/POST /api/faq`, `GET/PUT/DELETE /api/faq/{id}`, `GET/POST /api/faq/categorias`).
- Seed script (`scripts/seed_faq.py`) com ~20-30 perguntas de exemplo em pelo menos 3 categorias, incluindo variações propositais para testar similaridade depois.
- Critério de saída: CRUD funcional via `curl`/Swagger (`/docs` do FastAPI), seed populado.

## Parte 2 — Protótipos de busca por similaridade (backend, isolado)
- Definir interface comum `SimilarityService` com dois métodos: `find_best_match(pergunta: str) -> MatchResult | None` (usado pelo chat) e `vector_for(texto: str) -> Vector` (cada estratégia decide o que "vetor" significa).
- **Protótipo A (fuzzy)**: `pg_trgm` (extensão Postgres) ou `rapidfuzz` puro Python. `vector_for` retorna a representação em trigramas do texto normalizado.
- **Protótipo B (embedding)**: chamada à API OpenAI (`text-embedding-3-small`), cache de embeddings dos `FaqItem` (calculados no seed/CRUD, coluna `embedding`), comparação por cosseno. `vector_for` retorna o embedding real.
- **Protótipo C (híbrido)**: combina os scores de A e B (`score_final = α·score_embedding + (1-α)·score_trigram`), com `α` calibrado no mesmo script de avaliação.
- Normalização de texto (lowercase, remoção de acentuação/pontuação) antes de vetorizar, com cache de embedding por hash do texto normalizado.
- Limiar adaptativo: aceitar o melhor candidato por margem relativa ao segundo colocado, além do `SIMILARITY_THRESHOLD` absoluto.
- Gabarito fixo (`scripts/similarity_eval_dataset.json`): ~20 perguntas com `faq_item_id` esperado (`null` para as que devem cair em sem-resposta) — ~10 casos fáceis, ~5 paráfrases, ~5 com typos (composição detalhada no PRD §5).
- Script de avaliação (`scripts/eval_similarity.py`): roda o gabarito contra os três protótipos, calcula acurácia (% de match correto) e latência média por consulta, imprime tabela comparativa.
- Regra de decisão objetiva: vence maior acurácia; empate → menor latência. Sem julgamento subjetivo no momento de decidir.
- Decisão registrada no README com a tabela bruta do script (não só a conclusão).
- Critério de saída: script rodado, decisão tomada por essa regra e documentada, protótipo vencedor plugado como implementação padrão de `SimilarityService` (interface permite trocar via `SIMILARITY_BACKEND` no `.env`, então nenhum código é descartado).

## Parte 3 — Fluxo do chatbot (backend)
- `InteracaoRepository`: `create` e `get_unanswered` (listagem filtrada por `sem_resposta=true`, usada na Parte 5 para D3).
- `ChatService.ask(pergunta: str) -> ChatResponse`: recebe `SimilarityService` e `InteracaoRepository` injetados pelo construtor (via `Depends(...)` nas rotas — nenhum service instancia sua própria dependência), chama `find_best_match`, monta resposta ou fallback, grava `Interacao` (sempre, matched ou não).
- `api/chat.py`: `POST /api/chat/ask` — request `{pergunta}`, response `{resposta, faq_item_id, categoria, sem_resposta, score}`.
- Tratamento de erros: pergunta vazia (422), falha do provedor de embedding (fallback automático para fuzzy, não derruba o chat), timeout de API externa.
- Critério de saída: testes automatizados (pytest) cobrindo match, no-match e fallback de erro — usando repositório e `SimilarityService` fake injetados, sem subir banco real; endpoint testável via Swagger.

## Parte 4 — Interface de chat (frontend)
- `app/(chat)/page.tsx` + `components/domain/chat-window.tsx`: input, lista de mensagens (usuário/bot), indicador de "sem resposta" visualmente distinto.
- Integração via TanStack Query (`useMutation`) chamando `POST /api/chat/ask`.
- Estados: loading, erro de rede, resposta vazia.
- Critério de saída: conversa funcional end-to-end no browser, incluindo caso de pergunta sem match.

## Parte 5 — Métricas agregadas (backend)
- `TimeseriesMetricsRepository` (Postgres): `get_summary(date_from, date_to)` → total de consultas, total sem resposta, taxa de sem-resposta (D1); `get_daily_series(date_from, date_to)` → D5.
- `FaqMetricsRepository` (Postgres): `get_top_questions(date_from, date_to, limit)` → D2; `get_category_breakdown(date_from, date_to)` → D4.
- `InteracaoRepository.get_unanswered(date_from, date_to, limit)` (já existe desde a Parte 3) → D3, lista + contagem.
- `api/metrics.py`: um endpoint por query acima, todos aceitando `date_from`/`date_to` como query params opcionais (sem RBAC — não é requisito do desafio).
- Critério de saída: endpoints retornam dados corretos contra o seed da Parte 1 + interações geradas na Parte 3/4.

## Parte 6 — Autenticação do painel admin (backend + frontend)
- Backend: `AuthService` (gera OTP 6 dígitos TTL 5min single-use, envia por e-mail via `smtplib`/SMTP, valida OTP, emite JWT), `auth/otp_store.py` (armazenamento em memória — TTLCache, sem tabela dedicada), `auth/jwt.py` (emissão/validação do cookie de sessão).
- `api/auth.py`: `POST /api/auth/otp/request` (compara e-mail recebido com `ADMIN_EMAIL`; resposta genérica idêntica para "bate"/"não bate" — anti-enumeração; rate limit 3 tentativas/15min), `POST /api/auth/otp/verify` (valida OTP, seta cookie `httpOnly`/`secure`/`samesite=strict`).
- Dependency `require_admin_session` (`Depends`) protegendo `/api/faq/*` e `/api/metrics/*` — aplicada retroativamente aos endpoints das Partes 1 e 5.
- Frontend: `app/(auth)/login/page.tsx` (form de e-mail → form de OTP), `stores/auth-store.ts` (Zustand, estado de sessão), redirecionamento automático de `/dashboard/*` para `/login` quando sem sessão válida.
- Critério de saída: tentar acessar `/faq` ou `/metricas` sem login redireciona para `/login`; fluxo completo de solicitar OTP (e-mail chega de verdade via SMTP configurado), verificar, e navegar autenticado até o CRUD.

## Parte 7 — Dashboard (frontend)
- `app/(dashboard)/metricas/page.tsx`: cards de KPI (D1, D3), gráfico de série temporal (D5, `timeseries-chart.tsx` em Recharts, linha), gráfico de categoria (D4, `category-breakdown-chart.tsx` em Recharts, barra/pizza), tabela de perguntas mais frequentes (D2, componente `SimpleTable` reutilizável), lista de perguntas sem resposta (D3).
- Componente `DateInput` para filtro de período, reutilizado nas queries de métricas.
- Critério de saída: dashboard reflete em tempo real as interações geradas via chat; inacessível sem sessão (Parte 6).

## Parte 8 — Administração da base de conhecimento (frontend)
- `app/(dashboard)/faq/page.tsx`: listagem, criação, edição, remoção de `FaqItem`/`Categoria` — necessário para o avaliador conseguir alimentar a base e testar o chatbot sem acesso direto ao banco.
- Critério de saída: fluxo completo de cadastro de uma nova pergunta e verificação de que o chatbot passa a respondê-la.

## Parte 9 — Testes de frontend
- Vitest + Testing Library (já nas devDependencies do scaffold da Parte 0) cobrindo: `chat-window.tsx` (envio de pergunta, exibição de resposta, estado de "sem resposta"), `category-breakdown-chart.tsx`/`timeseries-chart.tsx` (renderiza com dados mock, não quebra com array vazio), `login-form`/`verify-form` (Parte 6 — submissão, erro de OTP inválido), `faq/page.tsx` (CRUD — criar, editar, excluir refletem na lista).
- Sem essa Parte, `pnpm test` no CI (`ci.yml`) passa por ausência de teste, não por cobertura — objetivo aqui é o CI validar algo real antes da Parte 10.
- Critério de saída: `pnpm test` roda com suíte não-vazia e cobre pelo menos os fluxos críticos acima; CI (`ci.yml`) reflete isso a partir deste ponto.

## Parte 10 — Polimento, erros e performance
- Tratamento de erro consistente (backend: exception handlers FastAPI → JSON padronizado; frontend: toasts/estados de erro em todas as queries/mutations via `sonner`).
- Validação de input (Pydantic no backend, Zod no frontend — já nas dependências).
- Paginação ou limite razoável nas listagens (FAQ admin, perguntas sem resposta) — volume aqui é pequeno, mas mostra boas práticas.
- Responsividade (checklist manual em mobile/desktop).
- Revisão de UX conforme `frontend-design`/`dataviz` skills antes de finalizar telas visuais.

## Parte 11 — Documentação e entrega
- `README.md`: contexto, stack, decisão de similaridade (com a tabela bruta do protótipo, não só a conclusão — PRD §5), como rodar (`docker compose up`), variáveis de ambiente (incluindo `ADMIN_EMAIL`/SMTP/`JWT_SECRET_KEY`), estrutura de pastas, comportamento de bootstrap automático (migration + seed no primeiro boot, PRD §10) e como resetar o banco para testar o cadastro do zero.
- Verificar todos os critérios de avaliação do PRD §4 como checklist final.
- Repositório GitHub público (ou conforme instrução do processo seletivo), commits organizados por parte/feature.
- CI/CD já configurado desde o início do projeto (build + gate de review automatizado, PRD §11) — evidência de execução do review fica em comentário na PR, não em arquivo versionado.

## Ordem recomendada de execução
0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11, com possibilidade de paralelizar 4 com 3 (frontend de chat com mock) e 7 com 5 (dashboard com mock) se quiser adiantar UI enquanto a API é fechada — mas dado que é solo, sequencial tende a ser mais previsível. Parte 6 (auth) precisa terminar antes de 7/8 ficarem "prontas de verdade" (a UI pode ser construída em paralelo, mas o gate de sessão é pré-requisito para considerar 7/8 completas).
