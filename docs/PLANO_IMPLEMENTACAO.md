# Plano de Implementação — Chatbot de FAQ com Dashboard Analítico

Referência: `PRD.md`. Cada parte é entregável e testável isoladamente antes de avançar para a próxima.

## Parte 0 — Scaffolding e infraestrutura
- Estrutura de pastas `backend/` e `frontend/` criadas do zero (`create-next-app` para o frontend, layout de pacote padrão para o backend FastAPI).
- `docker-compose.yml`: serviço `postgres`, `backend` (FastAPI + uvicorn), `frontend` (Next.js).
- `backend/config.py` via pydantic-settings: `DATABASE_URL`, `OPENAI_API_KEY`, `OPENAI_MODEL`, `SIMILARITY_BACKEND` (`fuzzy` | `embedding`), `SIMILARITY_THRESHOLD`.
- `.env.example` com todas as variáveis, sem valores reais.
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
- Definir interface comum `SimilarityService.find_best_match(pergunta: str) -> MatchResult | None`.
- **Protótipo A (fuzzy)**: `pg_trgm` (extensão Postgres) ou `rapidfuzz` puro Python.
- **Protótipo B (embedding)**: chamada à API OpenAI (`text-embedding-3-small`), cache de embeddings dos `FaqItem` (calculados no seed/CRUD, coluna `embedding`), comparação por cosseno.
- **Protótipo C (híbrido)**: combina os scores de A e B (`score_final = α·score_embedding + (1-α)·score_trigram`), com `α` calibrado no mesmo script de avaliação.
- Normalização de texto (lowercase, remoção de acentuação/pontuação) antes de vetorizar, com cache de embedding por hash do texto normalizado.
- Limiar adaptativo: aceitar o melhor candidato por margem relativa ao segundo colocado, além do `SIMILARITY_THRESHOLD` absoluto.
- Script de avaliação (`scripts/eval_similarity.py`): roda ~20 perguntas de teste (paráfrases e typos incluídos) contra os três protótipos, imprime taxa de acerto e latência média.
- Decisão registrada no README com a saída do script.
- Critério de saída: script rodado, decisão tomada e documentada, protótipo vencedor plugado como implementação padrão de `SimilarityService` (interface permite trocar via `SIMILARITY_BACKEND` no `.env`, então nenhum código é descartado).

## Parte 3 — Fluxo do chatbot (backend)
- `InteracaoRepository`: `create`, queries de agregação usadas na Parte 5.
- `ChatService.ask(pergunta: str) -> ChatResponse`: chama `SimilarityService`, monta resposta ou fallback, grava `Interacao` (sempre, matched ou não).
- `api/chat.py`: `POST /api/chat/ask` — request `{pergunta}`, response `{resposta, faq_item_id, categoria, sem_resposta, score}`.
- Tratamento de erros: pergunta vazia (422), falha do provedor de embedding (fallback automático para fuzzy, não derruba o chat), timeout de API externa.
- Critério de saída: testes automatizados (pytest) cobrindo match, no-match e fallback de erro; endpoint testável via Swagger.

## Parte 4 — Interface de chat (frontend)
- `app/(chat)/page.tsx` + `components/domain/chat-window.tsx`: input, lista de mensagens (usuário/bot), indicador de "sem resposta" visualmente distinto.
- Integração via TanStack Query (`useMutation`) chamando `POST /api/chat/ask`.
- Estados: loading, erro de rede, resposta vazia.
- Critério de saída: conversa funcional end-to-end no browser, incluindo caso de pergunta sem match.

## Parte 5 — Métricas agregadas (backend)
- `MetricsRepository` (Postgres):
  - `get_summary(date_from, date_to)` → total de consultas, total sem resposta, taxa de sem-resposta.
  - `get_top_questions(date_from, date_to, limit)` → D2.
  - `get_unanswered(date_from, date_to, limit)` → D3, lista + contagem.
  - `get_category_breakdown(date_from, date_to)` → D4.
  - `get_daily_series(date_from, date_to)` → D5 (contagem diária de interações no período).
- `ClusteringService.cluster_unanswered(date_from, date_to)` → agrupa as perguntas sem resposta por similaridade (reaproveitando `interacao.embedding`, quando o backend semântico está ativo) para expor temas recorrentes ainda não cobertos pela base — D3 avançado.
- `api/metrics.py`: um endpoint por query acima, todos aceitando `date_from`/`date_to` como query params opcionais (sem RBAC — não é requisito do desafio).
- Critério de saída: endpoints retornam dados corretos contra o seed da Parte 1 + interações geradas na Parte 3/4.

## Parte 6 — Dashboard (frontend)
- `app/(dashboard)/metricas/page.tsx`: cards de KPI (D1, D3), gráfico de série temporal (D5, `timeseries-chart.tsx` em Recharts, linha), gráfico de categoria (D4, `category-breakdown-chart.tsx` em Recharts, barra/pizza), tabela de perguntas mais frequentes (D2, componente `SimpleTable` reutilizável), lista de perguntas sem resposta agrupada por tema (D3, clusters do `ClusteringService`).
- Componente `DateInput` para filtro de período, reutilizado nas queries de métricas.
- Critério de saída: dashboard reflete em tempo real as interações geradas via chat.

## Parte 7 — Administração da base de conhecimento (frontend)
- `app/(dashboard)/faq/page.tsx`: listagem, criação, edição, remoção de `FaqItem`/`Categoria` — necessário para o avaliador conseguir alimentar a base e testar o chatbot sem acesso direto ao banco.
- Critério de saída: fluxo completo de cadastro de uma nova pergunta e verificação de que o chatbot passa a respondê-la.

## Parte 8 — Polimento, erros e performance
- Tratamento de erro consistente (backend: exception handlers FastAPI → JSON padronizado; frontend: toasts/estados de erro em todas as queries/mutations via `sonner`).
- Validação de input (Pydantic no backend, Zod no frontend — já nas dependências).
- Paginação ou limite razoável nas listagens (FAQ admin, perguntas sem resposta) — volume aqui é pequeno, mas mostra boas práticas.
- Responsividade (checklist manual em mobile/desktop).
- Revisão de UX conforme `frontend-design`/`dataviz` skills antes de finalizar telas visuais.

## Parte 9 — Documentação e entrega
- `README.md`: contexto, stack, decisão de similaridade (com números do protótipo), como rodar (`docker compose up`), variáveis de ambiente, estrutura de pastas.
- Verificar todos os critérios de avaliação do PRD §4 como checklist final.
- Repositório GitHub público (ou conforme instrução do processo seletivo), commits organizados por parte/feature.

## Ordem recomendada de execução
0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9, com possibilidade de paralelizar 4 com 3 (frontend de chat com mock) e 6 com 5 (dashboard com mock) se quiser adiantar UI enquanto a API é fechada — mas dado que é solo, sequencial tende a ser mais previsível.
