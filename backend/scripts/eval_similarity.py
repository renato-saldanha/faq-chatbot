"""Roda o gabarito de similaridade (docs/PRD.md §5) contra o SimilarityService ativo.

Mede acurácia por categoria de caso (caso_facil, parafrase, typo, sem_match) usando
o mesmo mecanismo do chat real (find_best_match do backend selecionado via
SIMILARITY_BACKEND) — não reimplementa a lógica de match, só chama a fronteira
pública do service.
"""

import asyncio
import json
import time
from pathlib import Path

from sqlalchemy import select

from app.api.chat import get_similarity_service
from app.db import async_session_maker
from app.models import FaqItem
from app.repositories.faq_repository import FaqRepository

DATASET_PATH = Path(__file__).parent / "similarity_eval_dataset.json"


async def resolve_expected_id(session, pergunta_esperada: str | None) -> int | None:
    if pergunta_esperada is None:
        return None
    result = await session.execute(select(FaqItem.id).where(FaqItem.pergunta == pergunta_esperada))
    row = result.scalar_one_or_none()
    return row


async def run() -> None:
    with open(DATASET_PATH, encoding="utf-8") as f:
        casos = json.load(f)

    service = get_similarity_service()
    resultados = []

    async with async_session_maker() as session:
        faq_repository = FaqRepository(session)
        for caso in casos:
            expected_id = await resolve_expected_id(session, caso["faq_pergunta_esperada"])

            start = time.perf_counter()
            match = await service.find_best_match(caso["pergunta"], faq_repository)
            elapsed_ms = (time.perf_counter() - start) * 1000

            got_id = match.faq_item_id if match else None
            acertou = got_id == expected_id

            resultados.append(
                {
                    "tipo": caso["tipo"],
                    "pergunta": caso["pergunta"],
                    "esperado": caso["faq_pergunta_esperada"],
                    "obtido": match.resposta[:50] if match else None,
                    "score": round(match.score, 3) if match else None,
                    "acertou": acertou,
                    "latencia_ms": round(elapsed_ms, 2),
                }
            )

    print(f"{'Tipo':<12} {'Acerto':<7} {'Score':<7} {'Latência':<10} Pergunta")
    print("-" * 90)
    for r in resultados:
        marca = "OK" if r["acertou"] else "FALHOU"
        score = f"{r['score']:.2f}" if r["score"] is not None else "-"
        print(f"{r['tipo']:<12} {marca:<7} {score:<7} {r['latencia_ms']:>7.2f}ms  {r['pergunta'][:45]}")

    print()
    por_tipo: dict[str, list[bool]] = {}
    for r in resultados:
        por_tipo.setdefault(r["tipo"], []).append(r["acertou"])

    total_acertos = sum(r["acertou"] for r in resultados)
    total_latencia = sum(r["latencia_ms"] for r in resultados)

    print(f"{'Categoria':<15} {'Acurácia':<12} Casos")
    print("-" * 40)
    for tipo, acertos in por_tipo.items():
        acc = sum(acertos) / len(acertos) * 100
        print(f"{tipo:<15} {acc:>6.1f}%      {sum(acertos)}/{len(acertos)}")

    print("-" * 40)
    print(f"{'TOTAL':<15} {total_acertos / len(resultados) * 100:>6.1f}%      {total_acertos}/{len(resultados)}")
    print(f"Latência média: {total_latencia / len(resultados):.2f}ms")


if __name__ == "__main__":
    asyncio.run(run())
