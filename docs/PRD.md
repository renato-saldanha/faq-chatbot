# PRD — Chatbot de FAQ com Dashboard Analítico

Status: rascunho v1
Base: `Desafio Full Stack 02 – Chatbot de FAQ com Dashboard Analítico.docx`

## 1. Contexto e objetivo (do enunciado, sem adaptação)

Empresas recebem alto volume de perguntas recorrentes de clientes/colaboradores/usuários, com respostas já conhecidas, mas que ainda consomem tempo da equipe de atendimento.

Objetivo: aplicação web com (a) **Chatbot de FAQ** que responde perguntas frequentes consultando uma base de conhecimento pré-cadastrada, e (b) **Dashboard Analítico** que coleta dados das interações do chatbot e apresenta indicadores de uso/comportamento para tomada de decisão.

Resultado esperado: automatizar o atendimento de dúvidas recorrentes + fornecer informação estratégica sobre comportamento dos usuários.

## 2. Escopo funcional (mapeado linha a linha do enunciado)

### 2.1 Chatbot

| # | Requisito do enunciado | Interpretação técnica |
|---|---|---|
| C1 | Consulta de perguntas e respostas cadastradas | Base de conhecimento (CRUD administrável) de pares pergunta↔resposta, com categoria |
| C2 | Busca eficiente por perguntas semelhantes | Não é match exato — precisa de similaridade textual/semântica (ver §5) |
| C3 | Exibição das respostas encontradas | UI de chat retorna a resposta do item mais similar acima de um limiar |
| C4 | Registro do histórico de interações | Toda pergunta recebida gera 1 registro de interação (matched ou não), com timestamp, pergunta, resposta (se houver), categoria, score de similaridade |
| C5 | Tratamento de perguntas sem resposta | Abaixo do limiar → resposta de fallback + registro marcado como `sem_resposta=true` |

### 2.2 Dashboard

| # | Requisito do enunciado | Interpretação técnica |
|---|---|---|
| D1 | Quantidade total de consultas realizadas | `COUNT(*)` de interações no período filtrado |
| D2 | Perguntas mais frequentes | Top-N por texto normalizado (ou por FAQ vinculada) |
| D3 | Perguntas sem resposta cadastrada | Lista/contagem de interações com `sem_resposta=true` — mesma fonte de C5, vista do lado dashboard. Quando `SIMILARITY_BACKEND` inclui embedding (protótipo B ou C), agrupadas por similaridade (clustering) para expor temas recorrentes ainda não cobertos pela base; com `SIMILARITY_BACKEND=fuzzy`, o `ClusteringService` cai para agrupamento por trigram sobre o texto normalizado — mesma interface, sem perder a funcionalidade (ver §7) |
| D4 | Distribuição de consultas por categoria | `GROUP BY categoria` — exige que toda pergunta da base tenha categoria (C1) |
| D5 | Evolução das consultas ao longo do tempo | Série diária de contagem de interações |
| D6 | Indicadores e gráficos para análise | Cards de KPI + gráficos (linha para D5, barra/pizza para D4, tabela para D2/D3) |

Fora do escopo do enunciado (não pede, não construir): autenticação multi-perfil/RBAC, múltiplos canais de atendimento (WhatsApp etc.), integração com BI externo, métricas de latência de infraestrutura (P50/P95) — nada disso é pedido pelo desafio.

## 3. Requisitos técnicos (do enunciado)

- IA permitida (opcional) na construção da aplicação e/ou na busca por similaridade.
- Frontend: **ReactJS** → decisão: **Next.js 14 (App Router)** + TypeScript, TanStack Query para data-fetching, Recharts para gráficos, Tailwind + Shadcn/ui para componentes.
- Backend: **Python ou NodeJS** → decisão: **FastAPI** (Python), com arquitetura em camadas (Repository → Service → API).
- Banco de dados → decisão: **PostgreSQL** — simples de containerizar, sem dependência de driver proprietário.
- Conteinerização: **Docker** (Dockerfile backend, Dockerfile frontend, `docker-compose.yml` com Postgres).
- Código no GitHub.

## 4. Critérios de avaliação (do enunciado — usar como checklist final)

Qualidade/organização do código · Arquitetura da solução · Organização do projeto · UX/UI · Performance · Boas práticas · Tratamento de erros e validações · Documentação e instruções de execução.

## 5. Decisão em aberto — busca por perguntas semelhantes

Construir **três protótipos comparáveis** antes de decidir o definitivo:

- **Protótipo A — léxico/fuzzy**: PostgreSQL `pg_trgm` (similaridade de trigramas) ou `rapidfuzz` em memória. Sem custo de API externa, determinístico, latência previsível. Ponto forte: erros de digitação e variações lexicais próximas. Ponto fraco: erra paráfrases com vocabulário muito diferente.
- **Protótipo B — semântico com IA**: embeddings via API da OpenAI (modelo barato, ex. `text-embedding-3-small`), comparação por cosseno. Ponto forte: pega paráfrases que o léxico erra ("como cancelo minha conta" vs "quero encerrar meu cadastro"). Ponto fraco: menos robusto a typos, depende de disponibilidade da API.
- **Protótipo C — híbrido**: combina os dois scores (`score_final = α·score_embedding + (1-α)·score_trigram`, `α` calibrado empiricamente). Mitiga o ponto fraco de cada abordagem isolada.

Refinamentos aplicados sobre o(s) protótipo(s) selecionado(s):
- **Normalização de texto antes de vetorizar**: lowercase, remoção de acentuação/pontuação, antes de gerar o embedding — reduz ruído e permite cache de embedding por hash do texto normalizado (evita recalcular para a mesma pergunta recorrente).
- **Limiar adaptativo em vez de fixo**: aceitar o melhor candidato não só por um `SIMILARITY_THRESHOLD` absoluto, mas também por margem relativa ao segundo colocado — evita aceitar um match fraco quando nada realmente parecido existe na base, e evita rejeitar um match bom em domínios onde o score absoluto tende a ser baixo.

**Critério de escolha — objetivo, não subjetivo:** um gabarito fixo de ~20 perguntas de teste (`scripts/similarity_eval_dataset.json`), cada uma com o `faq_item_id` esperado como resposta (ou `null` para as propositalmente sem match, testando C5). Composição do gabarito: ~10 perguntas próximas ao texto original da FAQ (caso fácil), ~5 paráfrases com vocabulário diferente (testa força do protótipo B/C), ~5 com erros de digitação (testa força do protótipo A). Rodar os três protótipos contra o mesmo gabarito e medir:
- **Acurácia** = (nº de respostas que batem com o `faq_item_id` esperado) / 20.
- **Latência média** por consulta.

**Regra de decisão:** vence o protótipo com maior acurácia; empate de acurácia → vence o de menor latência média. Resultado (acurácia, latência, protótipo vencedor) documentado no README com a tabela bruta do `scripts/eval_similarity.py`, não só a conclusão.

Chave de API em `.env` (`OPENAI_API_KEY`, `OPENAI_MODEL=gpt-4.1-mini` ou `text-embedding-3-small` conforme uso), nunca commitada — só `.env.example`.

Técnicas avaliadas e descartadas para este escopo (custo/complexidade não justificados pelo enunciado): reranking em duas etapas (cross-encoder ou LLM sobre os top-K candidatos) e expansão de consulta via paráfrases geradas por LLM.

## 6. Modelo de dados (proposto)

```
categoria
  id, nome, slug

faq_item
  id, categoria_id (FK), pergunta, resposta, ativo, criado_em, atualizado_em
  embedding (vector, nullable — presente quando protótipo B ou C for o backend ativo)

interacao
  id, pergunta_usuario, faq_item_id (FK, nullable), categoria_id (nullable, snapshot),
  score_similaridade, sem_resposta (bool), embedding (vector, nullable), criado_em
```

`interacao.faq_item_id` nullable + `sem_resposta` cobre C5/D3 na mesma tabela — não precisa de entidade separada para "perguntas sem resposta". `interacao.embedding` guarda o vetor da pergunta do usuário quando o backend semântico está ativo, reaproveitado depois para o clustering de perguntas sem resposta (D3) sem recalcular. `ClusteringService` nunca acessa esse campo diretamente — depende de `SimilarityService.vector_for(texto)` (ver §7), que cada estratégia implementa com sua própria noção de "vetor" (embedding real ou representação em trigramas), garantindo que D3 funcione com qualquer `SIMILARITY_BACKEND`.

## 7. Arquitetura

```
backend/ (FastAPI)
├── main.py                    # monta o app, registra dependency providers
├── config.py                  # pydantic-settings, inclui OPENAI_API_KEY/MODEL/ADMIN_EMAIL/SMTP_*
├── api/
│   ├── chat.py                 # POST /api/chat/ask (público)
│   ├── faq.py                  # CRUD da base de conhecimento (protegido — require_admin_session)
│   ├── auth.py                  # POST /api/auth/otp/request, POST /api/auth/otp/verify
│   └── metrics.py              # GET /api/metrics/summary|top-questions|unanswered|categories|timeseries (protegido)
├── services/
│   ├── similarity_service.py   # interface SimilarityService + 3 estratégias (fuzzy/embedding/híbrida)
│   ├── chat_service.py         # orquestra busca + registro de interação
│   ├── clustering_service.py   # agrupa perguntas sem resposta por similaridade (D3)
│   └── auth_service.py         # gera/valida OTP, emite JWT — single-admin via ADMIN_EMAIL
├── repositories/
│   ├── faq_repository.py
│   ├── interacao_repository.py
│   ├── faq_metrics_repository.py        # D2, D4 — leitura sobre faq_item/interacao por categoria/frequência
│   └── timeseries_metrics_repository.py # D1, D5 — leitura sobre interacao por período/dia
├── auth/
│   ├── otp_store.py             # OTP em memória (TTL 5min, single-use) — sem tabela dedicada
│   └── jwt.py                   # emissão/validação do cookie de sessão
└── models/ (SQLAlchemy) + alembic/

frontend/ (Next.js)
├── app/(chat)/page.tsx                 # interface de chat — pública
├── app/(auth)/login/page.tsx           # form de e-mail + OTP
├── app/(dashboard)/metricas/page.tsx   # cards + gráficos + tabelas — atrás de login
├── app/(dashboard)/faq/page.tsx        # CRUD admin da base de conhecimento — atrás de login
└── components/domain/
    ├── chat-window.tsx
    ├── category-breakdown-chart.tsx    # gráfico de barra/pizza (Recharts)
    └── timeseries-chart.tsx            # gráfico de linha (Recharts)

docker-compose.yml   # postgres + backend + frontend
```

### 7.1 Injeção de dependência

Nenhum service ou repository instancia suas próprias dependências. `Categoria`/`FaqItem`/`Interacao` repositories recebem a sessão de banco via `Depends(get_db_session)`; `ChatService` e `ClusteringService` recebem `SimilarityService` e os repositórios de que precisam pelo construtor, resolvidos por `Depends(...)` nas rotas do FastAPI (padrão nativo do framework — sem necessidade de container de DI externo). Isso é o que torna os services testáveis isoladamente com repositórios/estratégias fake nos testes da Parte 3.

### 7.2 Dependência declarada — `ClusteringService` → `SimilarityService`

D3 (perguntas sem resposta agrupadas por tema) depende de uma noção de "distância entre perguntas", que só existe dentro de `SimilarityService`. Para não acoplar o clustering a um backend específico, a interface expõe um método adicional:

```
SimilarityService.vector_for(texto: str) -> Vector
```

Cada estratégia implementa `vector_for` com sua própria representação — embedding real nos protótipos B/C, vetor esparso de trigramas no protótipo A. `ClusteringService` consome só essa interface, nunca a coluna `interacao.embedding` diretamente, então D3 funciona corretamente qualquer que seja o `SIMILARITY_BACKEND` escolhido ao final da Parte 2.

### 7.3 Métricas divididas por tipo de consulta

O que era um único `MetricsRepository` acumulando 5 responsabilidades de leitura foi dividido em dois repositórios menores por afinidade de consulta: `FaqMetricsRepository` (D2 perguntas mais frequentes, D4 distribuição por categoria — ambos agregam sobre `faq_item`/categoria) e `TimeseriesMetricsRepository` (D1 total, D5 série diária — agregam sobre `interacao` por período). `get_unanswered` (D3) vive em `InteractionRepository`, já que é uma listagem filtrada de `Interacao`, não uma agregação nova.

## 8. Fora de escopo (explicitamente, para não inflar o projeto)

- Autenticação multi-perfil / RBAC (o enunciado não pede login nem perfis).
- Canais externos (WhatsApp, etc).
- Integração com BI externo.
- Qualquer domínio de negócio alheio ao FAQ/chatbot descrito no enunciado.

## 9. Autenticação do painel admin (decisão de projeto — enunciado não exige, risco de deixar aberto)

O chat (`/chat`) é público, sem login — é o produto voltado ao usuário final, consistente com o enunciado. O painel admin (`/faq`, CRUD da base de conhecimento e categorias) fica **atrás de login via OTP por e-mail**, single-admin, sem tabela de usuários:

- `ADMIN_EMAIL` fixo no `.env` — único e-mail autorizado.
- Fluxo: usuário informa e-mail no form de login → backend compara com `ADMIN_EMAIL`; se bater, gera OTP (6 dígitos, TTL 5min, single-use) e envia por e-mail via SMTP; se não bater, mesma resposta genérica (evita enumerar se o e-mail é válido, mesmo princípio anti-enumeração de OTP já visto em sistemas de auth por telefone).
- Verificação do OTP → JWT em cookie `httpOnly`, `secure`, `samesite=strict` (nunca no body/localStorage).
- SMTP simples (`smtplib` — conta existente, senha de app), sem provedor de e-mail transacional dedicado — evita mais uma credencial paga além da já usada para similaridade (protótipo B/C).
- `/api/chat/*` continua público; `/api/faq/*` (CRUD) exige o cookie de sessão válido — dependency `require_admin_session` no FastAPI.
- Rate limit simples no endpoint de solicitar OTP (ex. 3 tentativas/15min) para não virar vetor de spam de e-mail.

Fora de escopo desta decisão: múltiplos admins, recuperação de conta, "lembrar de mim" além do TTL do JWT — nenhum desses é pedido pelo enunciado nem necessário para um único administrador fixo.

## 10. Bootstrap de dados no deploy

`docker compose up` precisa deixar a aplicação usável sem passo manual extra:
- Migration do Alembic roda automaticamente no boot do container `backend` (entrypoint aplica `alembic upgrade head` antes de subir o `uvicorn`), não como instrução manual no README.
- Seed da base de FAQ (`scripts/seed_faq.py`, criado na Parte 1) roda automaticamente no primeiro boot se a tabela `faq_item` estiver vazia — checagem idempotente, não recria em boots subsequentes. Sem isso, o avaliador abre o chat e não há nenhuma pergunta cadastrada para testar.
- README documenta esse comportamento explicitamente (Parte 9), incluindo como resetar o banco para testar o fluxo de admin cadastrando do zero, se o avaliador quiser.

<!-- validação: confirma que o gate de review roda sem bootstrap paradox neste PR -->

<!-- validacao: gate sem --agent, apos fix do PR #4 -->

<!-- validacao final: gate com execution_file + log persistido -->

<!-- validacao: allowedTools corrigido -->

<!-- teste: sem claude_args -->
