# Checklist de entrega — Chatbot de FAQ com Dashboard Analítico

Estado real do projeto contra as 12 Partes do `PLANO_IMPLEMENTACAO.md`, cruzado com commits, testes e o smoke test manual desta sessão — não com relatório de sessão anterior.

**Prazo:** 11h — 23/08/2026. **Status atual:** 11/12 partes completas.

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

- [x] **Parte 9 — Testes de frontend.** 28 testes Vitest + Testing Library cobrindo `chat-window` (8), gráficos `timeseries`/`category-breakdown` (4), `login-form`/`verify-form` (8), CRUD de `faq/page` (7), mais o placeholder original. Escritos em 4 agentes paralelos, cada um em worktree isolada, integrados via 5 PRs (#19-#23) revisados e mesclados. Infra de teste compartilhada extraída para `vitest.setup.ts` (cleanup automático + `ResizeObserver` stub) e `src/lib/test-utils.tsx` (`renderWithClient`) durante a integração, eliminando duplicação entre os PRs.

- [x] **Parte 10 — Polimento, erros e performance.** Bug real corrigido: `.data-table` com `display:block` quebrava o layout de colunas HTML em mobile (coluna "Ativo"/"Ações" cortada e ilegível) — trocado por wrapper `.table-scroll` com scroll horizontal real, validado em 375/768/1440px via Playwright headless. Redesign visual completo com paleta verde-petróleo/terracota (skills `frontend-design`/`dataviz`, cor validada via `validate_palette.js`), Fraunces + Inter + IBM Plex Mono, focus-visible e `prefers-reduced-motion` em todos os controles. Paginação nas listagens não implementada — volume do seed (15 itens) não justifica.

- [x] **Parte 11 — Documentação e entrega.** `README.md` com setup, env vars, decisão de similaridade, estrutura. Commits organizados por unidade lógica, enviados ao GitHub. `/code-review high` rodado sobre o diff inicial — sem achados.

## Cortado por decisão consciente (sob prazo)

- [~] **Parte 2 — Protótipos de similaridade.** Protótipo A (fuzzy, `rapidfuzz`) implementado e em produção. Protótipo B (embedding OpenAI) e C (híbrido) não implementados, script de avaliação comparativo não feito. Schema já suporta `embedding` via `pgvector` — extensível sem tocar em `ChatService`.

- [~] **CI/CD e testes E2E.** GitHub Actions com gate de review por IA — construído, depois desativado. Testes E2E automatizados (Playwright em CI) — só rodados ad-hoc nesta sessão. Branch protection removida, commits diretos na `master`. Workflows continuam no repo como referência.

## Pendente

Nenhuma parte pendente — só a checagem final abaixo.

## Se sobrar tempo, nesta ordem

1. **Checklist final do PRD §4** — conferir cada critério de avaliação verbatim do enunciado antes de considerar encerrado.
