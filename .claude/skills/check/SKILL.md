---
name: check
description: Roda localmente os mesmos gates do CI (ruff, mypy, pytest no backend; lint, typecheck, test, build no frontend) — mais rápido que esperar o GitHub Actions e pega o mesmo erro antes de commitar.
when_to_use: "Antes de marcar qualquer item do plano de implementação como concluído, e sempre antes de /before-push."
disable-model-invocation: true
allowed-tools: ["Bash(cd *)", "Bash(pip *)", "Bash(ruff *)", "Bash(mypy *)", "Bash(pytest *)", "Bash(pnpm *)"]
---

# /check — gates locais

Roda os mesmos checks que `ci.yml` roda no GitHub Actions, na ordem abaixo. Para no primeiro erro real (não continue rodando os próximos gates com um anterior vermelho — corrija primeiro).

## Backend (se `backend/` existir)

```bash
cd backend
ruff check .
ruff format --check .
mypy .
pytest -v
```

## Frontend (se `frontend/` existir)

```bash
cd frontend
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

## Docker (opcional, mais lento — rodar antes de PR que toca `docker-compose.yml`/Dockerfiles)

```bash
docker compose build
```

## Saída

Reporte no formato: gate → pass/fail. Se algum falhar, mostre o erro real (não resuma) e pare — não prossiga para o próximo gate nem para `/before-push` até o atual estar verde.
