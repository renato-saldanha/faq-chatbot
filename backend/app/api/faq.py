from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api._deps import require_admin_session
from app.db import get_db_session
from app.repositories.faq_repository import FaqRepository

router = APIRouter(prefix="/api/faq", tags=["faq"], dependencies=[Depends(require_admin_session)])


class CategoriaOut(BaseModel):
    id: int
    nome: str
    slug: str


class FaqItemOut(BaseModel):
    id: int
    categoria_id: int
    categoria_nome: str
    pergunta: str
    resposta: str
    ativo: bool


class FaqItemIn(BaseModel):
    categoria_id: int
    pergunta: str
    resposta: str
    ativo: bool = True


class CategoriaIn(BaseModel):
    nome: str
    slug: str


def get_faq_repository(session: AsyncSession = Depends(get_db_session)) -> FaqRepository:
    return FaqRepository(session)


def _to_out(item) -> FaqItemOut:
    return FaqItemOut(
        id=item.id,
        categoria_id=item.categoria_id,
        categoria_nome=item.categoria.nome,
        pergunta=item.pergunta,
        resposta=item.resposta,
        ativo=item.ativo,
    )


@router.get("", response_model=list[FaqItemOut])
async def list_faq(repo: FaqRepository = Depends(get_faq_repository)) -> list[FaqItemOut]:
    items = await repo.list_all(only_active=False)
    return [_to_out(i) for i in items]


@router.post("", response_model=FaqItemOut)
async def create_faq(body: FaqItemIn, repo: FaqRepository = Depends(get_faq_repository)) -> FaqItemOut:
    item = await repo.create(body.categoria_id, body.pergunta, body.resposta)
    return _to_out(item)


@router.put("/{faq_item_id}", response_model=FaqItemOut)
async def update_faq(
    faq_item_id: int, body: FaqItemIn, repo: FaqRepository = Depends(get_faq_repository)
) -> FaqItemOut:
    item = await repo.update(faq_item_id, body.categoria_id, body.pergunta, body.resposta, body.ativo)
    if item is None:
        raise HTTPException(status_code=404, detail="Pergunta não encontrada")
    return _to_out(item)


@router.delete("/{faq_item_id}")
async def delete_faq(faq_item_id: int, repo: FaqRepository = Depends(get_faq_repository)) -> dict[str, bool]:
    deleted = await repo.delete(faq_item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Pergunta não encontrada")
    return {"deleted": True}


@router.get("/categorias", response_model=list[CategoriaOut])
async def list_categorias(repo: FaqRepository = Depends(get_faq_repository)) -> list[CategoriaOut]:
    categorias = await repo.list_categorias()
    return [CategoriaOut(id=c.id, nome=c.nome, slug=c.slug) for c in categorias]


@router.post("/categorias", response_model=CategoriaOut)
async def create_categoria(
    body: CategoriaIn, repo: FaqRepository = Depends(get_faq_repository)
) -> CategoriaOut:
    categoria = await repo.create_categoria(body.nome, body.slug)
    return CategoriaOut(id=categoria.id, nome=categoria.nome, slug=categoria.slug)
