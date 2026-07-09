
class Produto:
    """
    Representa um produto no Problema do Caixeiro Viajante (TSP).

    Atributos
    ---------
    id         : int — identificador do produto
    nome       : str — nome do produto
    prioridade : int — 1 = alta urgência (vacinas/medicamentos), 2 = baixa urgência (insumos)
    peso_kg    : float — peso estimado da entrega em kg
    """

    def __init__(self, id: int, nome: str, prioridade: int, peso_kg: float = 0.0) -> None:
        if prioridade not in {1, 2}:
            raise ValueError(f"prioridade inválida: '{prioridade}'. Use 1 (alta) ou 2 (baixa).")
        if peso_kg < 0:
            raise ValueError(f"peso_kg inválido: '{peso_kg}'. Use um valor maior ou igual a 0.")
        self.id: int = id
        self.nome: str = nome
        self.prioridade: int = prioridade
        self.peso_kg: float = peso_kg

    def __eq__(self, outro: object) -> bool:
        return isinstance(outro, Produto) and self.id == outro.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        return f"Produto(id={self.id}, nome='{self.nome}', prioridade={self.prioridade}, peso_kg={self.peso_kg})"

    def __str__(self) -> str:
        return f"Produto: {self.nome} (Prioridade: {self.prioridade}, Peso: {self.peso_kg} kg)"
