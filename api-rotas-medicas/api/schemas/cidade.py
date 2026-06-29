from pydantic import BaseModel


class CidadeResponse(BaseModel):
    cod_ibge: int
    nome: str
    uf: str
    latitude: float
    longitude: float
    regiao_tradicional: str | None
