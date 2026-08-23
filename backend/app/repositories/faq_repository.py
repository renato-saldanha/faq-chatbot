from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Categoria, FaqItem


class FaqRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self, only_active: bool = True) -> list[FaqItem]:
        query = select(FaqItem).options(selectinload(FaqItem.categoria))
        if only_active:
            query = query.where(FaqItem.ativo.is_(True))
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, faq_item_id: int) -> FaqItem | None:
        query = select(FaqItem).options(selectinload(FaqItem.categoria)).where(FaqItem.id == faq_item_id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, categoria_id: int, pergunta: str, resposta: str) -> FaqItem:
        item = FaqItem(categoria_id=categoria_id, pergunta=pergunta, resposta=resposta, ativo=True)
        self._session.add(item)
        await self._session.commit()
        await self._session.refresh(item, attribute_names=["categoria"])
        return item

    async def update(
        self, faq_item_id: int, categoria_id: int, pergunta: str, resposta: str, ativo: bool
    ) -> FaqItem | None:
        item = await self.get_by_id(faq_item_id)
        if item is None:
            return None
        item.categoria_id = categoria_id
        item.pergunta = pergunta
        item.resposta = resposta
        item.ativo = ativo
        await self._session.commit()
        await self._session.refresh(item, attribute_names=["categoria"])
        return item

    async def delete(self, faq_item_id: int) -> bool:
        item = await self.get_by_id(faq_item_id)
        if item is None:
            return False
        await self._session.delete(item)
        await self._session.commit()
        return True

    async def list_categorias(self) -> list[Categoria]:
        result = await self._session.execute(select(Categoria))
        return list(result.scalars().all())

    async def create_categoria(self, nome: str, slug: str) -> Categoria:
        categoria = Categoria(nome=nome, slug=slug)
        self._session.add(categoria)
        await self._session.commit()
        await self._session.refresh(categoria)
        return categoria
