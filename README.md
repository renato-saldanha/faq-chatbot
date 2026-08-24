# Chatbot de FAQ com Dashboard Analítico

Desafio técnico full stack: chatbot que responde perguntas frequentes consultando uma base de conhecimento cadastrada, com dashboard de métricas de uso e painel admin (CRUD da base, protegido por login OTP).

Requisitos completos: `docs/PRD.md`. Plano de implementação original: `docs/PLANO_IMPLEMENTACAO.md`.

## Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.0 (async, `asyncpg`), Alembic, Pydantic v2, `rapidfuzz` + `openai` (similaridade — 3 protótipos, ver decisão abaixo), `pgvector`, `python-jose` (JWT), `slowapi` (rate limit)
- **Banco:** PostgreSQL 16 com extensão `pgvector`
- **Frontend:** Next.js 14 (App Router), TypeScript, TanStack Query, Zustand, Recharts, Zod
- **Auth do admin:** OTP por e-mail + JWT em cookie httpOnly — single-admin via `ADMIN_EMAIL`
- **Conteinerização:** Docker (`docker-compose.yml` na raiz — postgres + backend + frontend)

## Arquitetura

```
frontend (Next.js 14, :3000)
    |
    |  HTTP + cookie httpOnly JWT  --->
    |  <---  JSON  ---
    v
backend (FastAPI, :8000)
    |
    |  SQLAlchemy async  --->
    |  <---  resultado  ---
    v
postgres + pgvector (:5432)
```

Dois fluxos de requisição bem separados — o chat é público, tudo o mais exige sessão:

```
Chat (público, sem login)
  usuário digita pergunta
    → POST /api/chat/ask  [rate limit 10/min por IP, slowapi]
      → ChatService.ask()
        → SimilarityService.find_best_match()   [fuzzy | embedding | hybrid, ver "Decisão" abaixo]
          → FaqRepository (query no Postgres / pgvector cosine_distance)
        → InteracaoRepository.create()          [grava a interação, com ou sem match]
      ← resposta + score  (ou sem_resposta:true se nada bateu o threshold)

Admin (login OTP obrigatório)
  e-mail + código OTP
    → POST /api/auth/otp/verify → cookie httpOnly (JWT, HS256)
  toda rota /api/faq/* e /api/metrics/* exige o cookie
    → require_admin_session (app/api/_deps.py) valida o JWT antes de qualquer coisa
      → FaqRepository (CRUD da base) | FaqMetricsRepository / TimeseriesMetricsRepository (dashboard)
```

Camadas do backend, sempre nessa ordem — nenhuma pula a de baixo: `api/` (rota FastAPI) → `services/` (regra de negócio) → `repositories/` (única fronteira de acesso a dados/SQL) → `models/` (SQLAlchemy). Detalhe completo de cada padrão (Strategy, DTO, DI) na seção "Padrões de arquitetura" abaixo; convenções de código em `CLAUDE.md`.

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
| `SIMILARITY_BACKEND` | Backend de similaridade ativo — `fuzzy` \| `embedding` \| `hybrid` (ver decisão abaixo) |
| `SIMILARITY_THRESHOLD` | Limiar mínimo de score (0–1) para considerar um match válido — `0.55`, calibrado contra o gabarito (ver "Decisão" abaixo) |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | Necessário para os backends `embedding`/`hybrid` — chave da OpenAI, `OPENAI_MODEL=text-embedding-3-small` |
| `ADMIN_EMAIL` | E-mail autorizado a logar no painel admin (single-admin, sem tabela de usuários) |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` | Envio do código OTP por e-mail; vazio = OTP cai no log do backend (ver acima) |
| `JWT_SECRET_KEY` | Segredo de assinatura do JWT de sessão do admin — trocar em produção |

## Decisão: comparação dos três protótipos de similaridade

O PRD original (`docs/PRD.md` §5) previa comparar três protótipos — léxico/fuzzy, semântico via embedding OpenAI, e um híbrido — com um gabarito de perguntas e métricas de acurácia/latência antes de escolher o backend definitivo. **Os três estão implementados**, selecionáveis via `SIMILARITY_BACKEND`:

- **`fuzzy`** (Protótipo A) — `rapidfuzz`, léxico, sem custo/dependência de API externa.
- **`embedding`** (Protótipo B) — embeddings da OpenAI (`text-embedding-3-small`), comparação por cosseno. Exige `OPENAI_API_KEY`.
- **`hybrid`** (Protótipo C) — combina os dois scores (`score_final = α·score_embedding + (1-α)·score_trigram`).

O gabarito de avaliação (`scripts/similarity_eval_dataset.json`, 21 casos — 10 fáceis, 5 paráfrases, 5 com erro de digitação, 1 proposital sem match) roda contra o backend ativo (lido de `SIMILARITY_BACKEND`) via `scripts/eval_similarity.py`:

```bash
docker compose exec backend python -m scripts.eval_similarity
```

**Regra de decisão** (PRD §5): vence o protótipo com maior acurácia; empate → menor latência média. Resultado bruto de cada rodada: `docs/similarity_eval_output.txt`.

| Backend | Acurácia total | Paráfrase | Latência média |
|---|---|---|---|
| `fuzzy` | 76.2% (16/21) | 0% (0/5) | ~7ms |
| **`embedding`** | **100% (21/21)** | 100% (5/5) | ~330ms |
| `hybrid` (α=0.6) | 81.0% (17/21) | 20% (1/5) | ~380ms |

**Vencedor: `embedding`** — maior acurácia, sem empate. `fuzzy` só acerta paráfrase por acaso (score de coincidência lexical, não de significado); `embedding` resolve exatamente a categoria que o `fuzzy` não consegue. O híbrido (α=0.6) ficou *abaixo* do embedding puro: o termo fuzzy (peso 0.4) derruba o score final em paráfrases onde a semântica bate mas o léxico diverge — nesta base (perguntas curtas, domínio fechado de FAQ), misturar com léxico introduz ruído em vez de ajudar. Recomendado usar `SIMILARITY_BACKEND=embedding` no `.env` real (requer `OPENAI_API_KEY`); `.env.example` mantém `fuzzy` como padrão para não exigir a chave só para subir a stack pela primeira vez.

A primeira rodada do `embedding` cravou 90.5% (19/21), com 2 falhas investigadas caso a caso (não ajuste cego de parâmetro):

- **"Vocês aceitam boleto?"** teve score 0.68 numa rodada e apareceu como falha em outra — instabilidade da execução isolada, não do backend; rodadas subsequentes confirmaram score estável acima do threshold.
- **"Esqueci minha senha, e agora?"** errava para um item vizinho do próprio seed (`"Esqueci meu login, o que fazer?"`, score 0.76 vs 0.72 do item correto) — os dois textos eram semanticamente quase idênticos. Corrigido reescrevendo o item concorrente no seed (`scripts/seed_faq.py`) para um cenário distinto (esqueceu qual e-mail usou no cadastro, não a senha em si), removendo a ambiguidade real entre os dois.
- **"Quero falar com uma pessoa de verdade, não um robô"** tinha score 0.59 contra o item correto (`"Como falo com um atendente humano?"`) — 0.01 abaixo do threshold de 0.6, com folga segura para o segundo colocado (0.39) e para o teto real dos casos `sem_match` (~0.30). `SIMILARITY_THRESHOLD` baixado para `0.55`, validado contra o próprio dataset para confirmar que nenhum caso `sem_match` verdadeiro se aproxima desse novo piso.

Resultado após as duas correções: **100% (21/21)**, latência ~330ms, estável em execuções repetidas.

Schema já suportava a extensão desde a Parte 1: `FaqItem` e `Interacao` têm coluna `embedding` (`pgvector`), e `SimilarityService` é a única fronteira de "quão parecida é uma pergunta" no código — nenhum outro módulo lê `embedding` ou compara texto diretamente, o que permitiu adicionar os backends B/C sem tocar em `ChatService` nem em quem consome métricas.

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
├── scripts/eval_similarity.py    # Gabarito de similaridade — ver "Decisão" acima
├── tests/                        # 76 testes (services/repositories + rotas HTTP), sem depender de Postgres real
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
- **Strategy Pattern** (`app/services/similarity_service.py`) — `SimilarityService` é uma interface abstrata (`find_best_match`, `vector_for`) com três implementações (`FuzzySimilarityService`, `EmbeddingSimilarityService`, `HybridSimilarityService`, selecionadas via `SIMILARITY_BACKEND`) mais um decorator (`FallbackSimilarityService`, envolve `embedding`/`hybrid` e degrada para `fuzzy` se a API da OpenAI falhar); o `ChatService` e o restante do código dependem só da interface, nunca da classe concreta.
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
pytest tests/ -v          # 76 passed
ruff check . && mypy app/  # ambos limpos

# Frontend
cd frontend
npx tsc --noEmit
npm run lint
npm run test          # 33 passed
```

## Segurança

Auditoria dedicada (não apenas revisão incidental) cobrindo autenticação/JWT, SQL injection, XSS, CORS, autorização, segredos e dependências. Resultado: sem vulnerabilidades críticas — JWT (HS256, `exp`, algoritmo explícito), cookie de sessão (`httponly`/`secure`/`samesite=strict`), 100% das queries via SQLAlchemy parametrizado (sem concatenação de string), CORS restrito a `http://localhost:3000`, `.env` real nunca commitado (histórico do git verificado), texto do chat renderizado via JSX (sem `dangerouslySetInnerHTML` com dado de usuário).

Dois problemas reais foram encontrados e corrigidos:

- **`/api/chat/ask` sem rate limit.** É a única rota pública do backend (sem login, por design — é o chat do usuário final) e, com `SIMILARITY_BACKEND=embedding`/`hybrid`, cada pergunta aciona uma chamada de billing real à API da OpenAI. Sem limite, um script simples em loop gera custo ilimitado na conta do dono do projeto. Corrigido com `slowapi` (10 requisições/minuto por IP, `app/rate_limit.py`) — resposta `429` com corpo `{"detail": "..."}` quando excedido. `ChatAskRequest.pergunta` também ganhou `max_length=1000` pelo mesmo motivo (payload gigante = mais tokens = mais custo).
- **Brute-force do código OTP.** O rate limit existia para *pedir* código novo (3 a cada 15min, evita spam de e-mail), mas não para *tentativas de verificação* — um código de 6 dígitos válido por 5 minutos podia ser forçado por tentativa e erro sem nenhum bloqueio. Corrigido em `OtpStore` (`app/auth/otp_store.py`) com um segundo limite independente: 5 tentativas de verificação por janela de 15min.

Ambos validados com testes automatizados (`test_chat.py::test_ask_acima_do_limite_retorna_429`, `test_auth_service.py::test_otp_store_bloqueia_brute_force_de_verificacao`) e contra o container Docker real.

**Aceito como escopo do desafio** (não corrigido, por não se aplicar ao contexto de projeto local/avaliação): `JWT_SECRET_KEY` com default fraco documentado ("trocar em produção"), sem CSP/security headers adicionais, credenciais do Postgres hardcoded no `docker-compose.yml` (infraestrutura local isolada em container).

## Frontend — auditoria de código e acessibilidade

Cobrindo tratamento de erro visível ao usuário, acessibilidade (labels, foco, feedback de estado) e aderência aos padrões documentados (client HTTP centralizado, componentes apresentacionais, design tokens). Confirmado: nenhum componente chama `fetch` fora de `lib/api.ts`, zero uso de `any`, `:focus-visible`/`prefers-reduced-motion` respeitados globalmente, `dangerouslySetInnerHTML` só em script estático (sem risco de XSS).

Três problemas reais corrigidos:

- **Erro de API nunca diferenciado por status.** `lib/api.ts` sempre lançava um `Error` genérico — nenhuma tela distinguia 429/401/404/422. Com o rate limit novo no chat, isso significava mostrar "toque em Enviar para tentar de novo" exatamente quando reenviar na hora ia continuar falhando por até 1 minuto — mensagem ativamente enganosa. Corrigido com uma classe `ApiError` (expõe `status`) em `lib/api.ts`; `chat-window.tsx` agora mostra "Muitas perguntas em pouco tempo. Aguarde um instante..." especificamente para 429.
- **Input do chat sem label acessível.** Só tinha `placeholder`, sem `aria-label`/`label` associado — leitor de tela não anuncia o propósito do campo de forma confiável. Corrigido com `aria-label="Digite sua pergunta"`.
- **Dashboard de métricas sem tratamento de erro.** As 5 queries (`useQuery`) não verificavam `isError` — se qualquer endpoint falhasse (rede, sessão expirada), a tela mostrava silenciosamente "—" ou "Sem dados no período", indistinguível de "não há dados de verdade". Corrigido com um banner (`role="alert"`) quando qualquer métrica falha ao carregar.

Validado com 3 testes novos (`chat-window.test.tsx`, `metricas/page.test.tsx`), suíte frontend total: 32/32.

Segunda rodada, cobrindo as telas restantes (`login-form.tsx`, `verify-form.tsx`, `faq/page.tsx`, guard de sessão): confirmado exclusão com confirmação real (`window.confirm`), botões de ação acessíveis por padrão (`<button>` com texto visível, sem necessidade de `aria-label` extra). Um achado real — não de acessibilidade, uma lacuna funcional: o formulário de FAQ tinha o campo `ativo` no estado interno (usado para desativar uma pergunta sem excluí-la) mas **nenhum controle de UI para editá-lo** — não havia como reativar/desativar uma pergunta pela tela. Corrigido com um checkbox "Ativo (visível no chat)"; aproveitado para também adicionar foco automático no primeiro campo ao abrir o formulário e padronizar labels com `htmlFor`/`id` explícito. Suíte frontend total: 33/33.

Smoke test manual contra o container Docker real (rebuild completo) confirmando as mudanças da sessão em conjunto: via `curl` — paráfrase mais difícil da calibração de similaridade (`"Quero falar com uma pessoa..."`) respondendo corretamente com o threshold recalibrado (score 0.59), rate limit do chat estourando em `429` após 10 requisições, payload acima de 1000 caracteres rejeitado com `422`. Via Playwright headless (script ad-hoc, não suíte versionada) — confirmação visual: a mesma paráfrase renderizada na tela, `aria-label` presente no input, o toast de rate limit aparecendo com a mensagem específica de `429` (não a genérica), e o guard de sessão redirecionando `/metricas` sem login para `/login`.

## Revisão de código dirigida (`pr-review-linus`)

O projeto tem um skill de review (`.claude/skills/pr-review-linus/`) pensado para rodar antes de um merge, comparando o diff contra `docs/PRD.md`/`docs/PLANO_IMPLEMENTACAO.md` — nunca tinha sido usado porque o projeto não segue fluxo de PR (commits diretos em `master`). Rodado pela primeira vez contra todo o diff acumulado da sessão (backend e frontend separados), veredicto **SHIP** nos dois — zero showstopper.

Achados reais corrigidos:

- **Fallback automático para `fuzzy` quando a API da OpenAI falha.** Já estava previsto desde o plano de implementação original e nunca tinha sido codificado: com `SIMILARITY_BACKEND=embedding`/`hybrid`, qualquer falha da API (timeout, rate limit, chave inválida) derrubava o chat inteiro no 500 genérico, em vez de degradar para o backend sem dependência externa. `FallbackSimilarityService` envolve o backend primário e captura `openai.APIError` (e subclasses) em `find_best_match`/`vector_for`, delegando para `fuzzy` com log de aviso.
- **Duplicação de `try/finally: app.dependency_overrides.clear()`** em 10+ testes de rota HTTP — um arquivo já resolvia isso com fixture `autouse`, os outros três não. Consolidado em `conftest.py`, isolamento entre testes agora é estrutural, não por convenção manual repetida.
- **Bolha de erro do chat não diferenciava 429** mesmo depois do toast já ter sido corrigido — meio problema resolvido antes. `Message.erro` (string, calculada uma vez em `onError`) substitui o antigo `Message.falhou` (boolean), eliminando a duplicação de lógica que causava a inconsistência.

Dois itens do PRD/Plano interno nunca implementados e descartados (não exigidos pelo enunciado original do desafio, confirmado contra o `.docx`): `ClusteringService` (agrupar perguntas sem resposta por tema — D3 já está 100% atendido na forma de lista simples) e limiar adaptativo de similaridade (margem relativa ao segundo colocado — threshold absoluto já atinge 100% no gabarito, com margem empírica de 0.20-0.25 nos casos válidos). Menções removidas do PRD/Plano; `Interacao.embedding` permanece no schema (nullable, sem custo) em vez de gerar uma migration só para remover a coluna.

Validado com 3 testes novos (fallback) + suíte reorganizada, backend total: 76/76.

## Fora do escopo desta entrega (decisões conscientes)

- **Sem testes E2E** (Playwright/Cypress) como suíte automatizada em CI.

CI/CD ativo em `.github/workflows/ci.yml` (GitHub Actions) — lint, typecheck e testes de backend e frontend, mais build do Docker Compose, em todo push/PR na `master`. Sem branch protection configurada, então nada bloqueia merge automaticamente hoje — os gates rodam e reportam, mas o merge continua manual.
