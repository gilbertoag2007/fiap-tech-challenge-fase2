from fastapi import APIRouter, HTTPException, Query

from api.schemas.produto import ProdutoResponse
from services.produto_service import produto_service

router = APIRouter(prefix="/produtos", tags=["Produtos"])


def _serializar(produto) -> dict:
    return {
        "id": produto.id,
        "nome": produto.nome,
        "prioridade": produto.prioridade,
    }


@router.get("/", response_model=list[ProdutoResponse])
def listar_todos():
    """Retorna todos os produtos carregados do CSV."""
    return [_serializar(p) for p in produto_service.listar_todos()]


@router.get("/pesquisar", response_model=list[ProdutoResponse])
def pesquisar_por_nome(termo: str = Query(..., min_length=1, description="Fragmento do nome do produto")):
    """Busca produtos cujo nome contenha o termo informado."""
    return [_serializar(p) for p in produto_service.pesquisar_por_nome(termo)]


@router.get("/{id}", response_model=ProdutoResponse)
def buscar_por_id(id: int):
    """Retorna o produto com o id informado."""
    produto = produto_service.buscar_por_id(id)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return _serializar(produto)
