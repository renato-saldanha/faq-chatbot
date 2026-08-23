# Checklist de entrega — Chatbot de FAQ com Dashboard Analítico

Estado real do projeto contra as 12 Partes do `PLANO_IMPLEMENTACAO.md`, cruzado com commits, testes e o smoke test manual desta sessão — não com relatório de sessão anterior.

**Prazo:** 11h — 23/08/2026. **Status atual:** 9/12 partes completas, 4 commits enviados a `origin/master`, `/code-review high` sem achados.

## Feito e validado

- [x] **Parte 0 — Scaffolding e infraestrutura.** Backend FastAPI + Frontend Next.js estruturados. `docker-compose.yml` com postgres + backend + frontend. Entrypoint roda migration + seed antes do uvicorn. `docker compose up --build` validado de ponta a ponta.

- [x] **Parte 1 — Modelo de dados e base de conhecimento.** Models `Categoria`/`FaqItem`/`Interacao` + migration inicial. CRUD REST completo de FAQ, testado via UI real. Seed idempotente — 15 perguntas em 3 categorias.
  - *Corrigido hoje:* FK de `interacao` sem `ondelete` bloqueava exclusão de qualquer FAQ já perguntada no chat.

- [x] **Parte 3 — Fluxo do chatbot.** `ChatService.ask()` com match, fallback e gravação de interação. `POST /api/chat/ask` respondendo corretamente via smoke test. Pergunta sem match retorna `sem_resposta: true`.
  - *Corrigido hoje:* crash `MissingGreenlet` ao ler `categoria` — trocado `join()` por `selectinload()`.

- [x] **Parte 4 — Interface de chat.** Chat público em `/`, sem login. Loading, badge de "sem resposta", integração TanStack Query. Testado ponta a ponta com Playwright headless.
  - *Corrigido hoje:* `app/page.tsx` duplicava a rota `/` já servida pelo route group `(chat)` — quebrava o build estático.

- [x] **Parte 5 — Métricas agregadas.** Resumo, série temporal, top perguntas, categoria, sem-resposta. Endpoints em `/api/metrics/*`, protegidos por sessão.

- [x] **Parte 6 — Autenticação do painel admin.** OTP 6 dígitos + JWT em cookie httpOnly, single-admin. Fluxo completo testado: pedir código → ler no log → validar → sessão ativa.
  - *Corrigido hoje:* guard do dashboard redirecionava para `/login` mesmo autenticado — Zustand `persist` lido antes da hidratação terminar.

- [x] **Parte 7 — Dashboard.** Cards de KPI, série temporal, breakdown por categoria (Recharts). Carrega sem crash, protegido por sessão — confirmado no smoke test.

- [x] **Parte 8 — Administração da base de conhecimento.** Criar → aparece na tabela → reflete no chat, testado ponta a ponta. Excluir FAQ já perguntada — confirmado funcionando após o fix de FK.

- [x] **Parte 11 — Documentação e entrega.** `README.md` com setup, env vars, decisão de similaridade, estrutura. 4 commits organizados por unidade lógica, enviados ao GitHub. `/code-review high` rodado sobre o diff — sem achados.

## Cortado por decisão consciente (sob prazo)

- [~] **Parte 2 — Protótipos de similaridade.** Protótipo A (fuzzy, `rapidfuzz`) implementado e em produção. Protótipo B (embedding OpenAI) e C (híbrido) não implementados, script de avaliação comparativo não feito. Schema já suporta `embedding` via `pgvector` — extensível sem tocar em `ChatService`.

- [~] **CI/CD e testes E2E.** GitHub Actions com gate de review por IA — construído, depois desativado. Testes E2E automatizados (Playwright em CI) — só rodados ad-hoc nesta sessão. Branch protection removida, commits diretos na `master`. Workflows continuam no repo como referência.

## Pendente

- [ ] **Parte 9 — Testes de frontend.**
  - [ ] `chat-window.tsx` — envio, resposta, estado sem-resposta
  - [ ] Gráficos — renderiza com mock, não quebra com array vazio
  - [ ] `login-form`/`verify-form` — submissão, OTP inválido
  - [ ] `faq/page.tsx` — CRUD reflete na lista
  - Cobertura atual: só `utils.test.ts` placeholder. Todo o fluxo já foi validado manualmente via Playwright headless, mas não como suíte permanente.

- [ ] **Parte 10 — Polimento, erros e performance.**
  - [ ] Checklist manual de responsividade mobile/desktop
  - [ ] Revisão de UX final (skills `frontend-design`/`dataviz`)
  - [ ] Paginação/limites nas listagens — volume atual é pequeno
  - Tratamento de erro e validação de input (Pydantic/Zod) já existem desde as Partes 1–8.

## Se sobrar tempo, nesta ordem

1. **Testes de frontend (Parte 9)** — zero cobertura real hoje, maior risco de regressão silenciosa em telas já validadas manualmente.
2. **Responsividade e polimento (Parte 10)** — UX/UI é critério de avaliação explícito do desafio.
3. **Checklist final do PRD §4** — conferir cada critério de avaliação verbatim do enunciado antes de considerar encerrado.
