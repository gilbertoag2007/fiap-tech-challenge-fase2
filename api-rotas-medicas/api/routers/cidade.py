from fastapi import APIRouter, HTTPException, Query

from api.schemas.cidade import CidadeResponse
from services.cidade_service import cidade_service

router = APIRouter(prefix="/cidades", tags=["Cidades"])


def _serializar(cidade) -> dict:
    return {
        "cod_ibge": cidade.cod_ibge,
        "nome": cidade.nome,
        "uf": cidade.uf,
        "latitude": cidade.latitude,
        "longitude": cidade.longitude,
        "regiao_tradicional": cidade.regiao_tradicional,
    }


@router.get("/", response_model=list[CidadeResponse])
def listar_todas():
    """Retorna todos os municípios carregados do CSV do IBGE."""
    return [_serializar(c) for c in cidade_service.listar_todas()]


@router.get("/pesquisar", response_model=list[CidadeResponse])
def pesquisar_por_nome(termo: str = Query(..., min_length=1, description="Fragmento do nome da cidade")):
    """Busca municípios cujo nome contenha o termo informado."""
    return [_serializar(c) for c in cidade_service.pesquisar_por_nome(termo)]


@router.get("/uf/{uf}", response_model=list[CidadeResponse])
def listar_por_uf(uf: str):
    """Retorna municípios de uma UF (ex.: SP, RJ)."""
    return [_serializar(c) for c in cidade_service.listar_por_uf(uf)]


@router.get("/regiao/{regiao}", response_model=list[CidadeResponse])
def listar_por_regiao_tradicional(regiao: str):
    """Retorna municípios pertencentes à região tradicional informada."""
    return [_serializar(c) for c in cidade_service.listar_por_regiao_tradicional(regiao)]


@router.get("/{cod_ibge}", response_model=CidadeResponse)
def buscar_por_cod_ibge(cod_ibge: int):
    """Retorna o município com o código IBGE informado."""
    cidade = cidade_service.buscar_por_cod_ibge(cod_ibge)
    if not cidade:
        raise HTTPException(status_code=404, detail="Cidade não encontrada.")
    return _serializar(cidade)
