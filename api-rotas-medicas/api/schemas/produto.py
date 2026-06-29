from pydantic import BaseModel


class ProdutoResponse(BaseModel):
    id: int
    nome: str
    prioridade: int
