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
| D3 | Perguntas sem resposta cadastrada | Lista/contagem de interações com `sem_resposta=true` — mesma fonte de C5, vista do lado dashboard. Agrupadas por similaridade (clustering sobre os embeddings já calculados) para expor temas recorrentes ainda não cobertos pela base, em vez de uma lista crua |
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

Critério de escolha: rodar as mesmas ~20 perguntas de teste (algumas parafraseadas, algumas com typos) contra os três protótipos, comparar taxa de acerto e latência, documentar no README a decisão final. Chave de API em `.env` (`OPENAI_API_KEY`, `OPENAI_MODEL=gpt-4.1-mini` ou `text-embedding-3-small` conforme uso), nunca commitada — só `.env.example`.

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

`interacao.faq_item_id` nullable + `sem_resposta` cobre C5/D3 na mesma tabela — não precisa de entidade separada para "perguntas sem resposta". `interacao.embedding` guarda o vetor da pergunta do usuário quando o backend semântico está ativo, reaproveitado depois para o clustering de perguntas sem resposta (D3) sem recalcular.

## 7. Arquitetura

```
backend/ (FastAPI)
├── main.py
├── config.py                  # pydantic-settings, inclui OPENAI_API_KEY/MODEL
├── api/
│   ├── chat.py                 # POST /api/chat/ask
│   ├── faq.py                  # CRUD da base de conhecimento
│   └── metrics.py              # GET /api/metrics/summary|categories|top-questions|unanswered|timeseries
├── services/
│   ├── similarity_service.py   # protótipos A/B/C (fuzzy, embedding, híbrido) por trás de uma interface comum
│   ├── chat_service.py         # orquestra busca + registro de interação
│   └── clustering_service.py   # agrupa perguntas sem resposta por similaridade (D3)
├── repositories/
│   ├── faq_repository.py
│   ├── interaction_repository.py
│   └── metrics_repository.py   # queries agregadas
└── models/ (SQLAlchemy) + alembic/

frontend/ (Next.js)
├── app/(chat)/page.tsx                 # interface de chat
├── app/(dashboard)/metricas/page.tsx   # cards + gráficos + tabelas
├── app/(dashboard)/faq/page.tsx        # CRUD admin da base de conhecimento
└── components/domain/
    ├── chat-window.tsx
    ├── category-breakdown-chart.tsx    # gráfico de barra/pizza (Recharts)
    └── timeseries-chart.tsx            # gráfico de linha (Recharts)

docker-compose.yml   # postgres + backend + frontend
```

## 8. Fora de escopo (explicitamente, para não inflar o projeto)

- Autenticação multi-perfil / RBAC (o enunciado não pede login nem perfis).
- Canais externos (WhatsApp, etc).
- Integração com BI externo.
- Qualquer domínio de negócio alheio ao FAQ/chatbot descrito no enunciado.
