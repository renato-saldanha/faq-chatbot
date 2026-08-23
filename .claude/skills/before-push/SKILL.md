---
name: before-push
description: Checklist obrigatório antes de git push — roda /check, dispara os agentes de domínio relevantes conforme o que mudou, e confirma que nada crítico ficou para trás. Adaptação enxuta do mapping usado em projetos maiores, calibrada para os 4 agentes deste projeto.
when_to_use: "Sempre antes de git push em qualquer branch, mesmo mudança pequena."
disable-model-invocation: true
allowed-tools: ["Bash(git *)", "Read", "Grep", "Glob", "Agent"]
---

# /before-push — checklist pré-push

## Passo 1 — `/check`

Rode a skill `check` primeiro. Só prossiga se todos os gates estiverem verdes.

## Passo 2 — Mapear arquivos alterados para agentes

```bash
git diff origin/master...HEAD --name-only
```

| Path alterado | Agente a disparar |
|---|---|
| `backend/api/**`, `backend/services/**`, `backend/repositories/**`, `backend/models/**` | `backend-reviewer` |
| `frontend/src/app/**`, `frontend/src/components/**` | `frontend-reviewer` |
| `backend/auth/**`, `backend/api/auth.py`, `backend/api/chat.py`, `backend/services/auth_service.py`, `backend/services/chat_service.py` | `security-reviewer` (além do `backend-reviewer`, se também bater no path acima) |
| Qualquer mudança em produção sem teste correspondente no mesmo diff | `test-writer` |

Um arquivo pode disparar mais de um agente — dispare todos os que se aplicam, em paralelo (múltiplas chamadas de `Agent` na mesma mensagem).

## Passo 3 — Rodar os agentes mapeados

Cada agente lê `docs/PRD.md`/`docs/PLANO_IMPLEMENTACAO.md` e o diff, retorna achados classificados como Showstopper/Concern.

## Passo 4 — Consolidar

- **Showstopper de qualquer agente → corrigir antes de push.** Sem exceção "trivial demais".
- **Concern → registrar na descrição do PR como débito consciente**, não silenciar.
- Se nenhum agente foi disparado (mudança só em `docs/`, `.github/`, etc.) — declare isso explicitamente, não pule o passo silenciosamente.

## Passo 5 — Push

Só depois de Showstoppers zerados. O gate remoto (`pr-review.yml`, agente `pr-reviewer` genérico) ainda roda no PR — este checklist é a primeira linha de defesa, mais rápida e mais específica por domínio; não substitui o gate de CI, complementa.

## Checklist final (responda cada item em texto explícito, sem "óbvio"/"trivial")

```
[ ] /check rodou e está verde?
[ ] Arquivos alterados mapeados para agentes — lista exata de quais rodaram?
[ ] Algum Showstopper? Se sim, corrigido antes deste ponto?
[ ] Concerns (se houver) vão para a descrição do PR?
```
