from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Interacao
from app.repositories._date_filter import apply_date_range


class InteracaoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        pergunta_usuario: str,
        faq_item_id: int | None,
        categoria_id: int | None,
        score: float | None,
        sem_resposta: bool,
    ) -> Interacao:
        interacao = Interacao(
            pergunta_usuario=pergunta_usuario,
            faq_item_id=faq_item_id,
            categoria_id=categoria_id,
            score_similaridade=score,
            sem_resposta=sem_resposta,
        )
        self._session.add(interacao)
        await self._session.commit()
        await self._session.refresh(interacao)
        return interacao

    async def get_unanswered(
        self,
        date_from: date | None = None,
        date_to: date | None = None,
        limit: int = 50,
    ) -> list[Interacao]:
        query = select(Interacao).where(Interacao.sem_resposta.is_(True))
        query = apply_date_range(query, date_from, date_to)
        query = query.order_by(Interacao.criado_em.desc()).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())
