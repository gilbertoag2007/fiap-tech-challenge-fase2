
class Produto:
 """
    Representa um produto no Problema do Caixeiro Viajante (TSP).
    Atributos
    ---------
    nome       : str        — nome do produto
    prioridade         : int        — prioridade do produto (1 = alta e 2 = baixa)
    """
 def __init__(
        self,
        nome: str,
        prioridade: int,
    ) -> None:
      
        if prioridade not in {1, 2}:
            raise ValueError(f"prioridade inválida: '{prioridade}'. Use 1 (alta) ou 2 (baixa).")
        self.nome: str = nome
        self.prioridade: int = prioridade

# ------------------------------------------------------------------
# Utilitários
# ------------------------------------------------------------------

def __eq__(self, outro: object) -> bool:
    """Dois produtos são iguais se tiverem o mesmo nome."""
    return isinstance(outro, Produto) and self.nome == outro.nome

def __hash__(self) -> int:
    """Permite usar Produto em sets e como chave de dicionário."""
    return hash(self.nome)

def __repr__(self) -> str:
    return (
        f"Produto(nome='{self.nome}', prioridade={self.prioridade})"
    )

def __str__(self) -> str:
    return f"Produto: {self.nome} (Prioridade: {self.prioridade})"