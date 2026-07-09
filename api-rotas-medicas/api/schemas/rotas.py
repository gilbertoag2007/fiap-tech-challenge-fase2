from typing import Literal

from pydantic import BaseModel, Field, model_validator


class RotasRequest(BaseModel):
    """
    Schema para a requisição de rotas médicas.
    """
    mensagem: str = Field(
        ...,
        min_length=20,
        max_length=500,
        description="Mensagem descritiva com a lista de cidades e produtos a serem entregues na rota a ser otimizada.",
    )
    epocas: int = Field(
        default=1,
        ge=1,
        le=100_000,
        description="Número de épocas para o algoritmo genético.",
    )
    elitismo: int = Field(
        default=1,
        ge=0,
        le=1,
        description="Indica se o elitismo deve ser aplicado (1=sim, 0=não).",
    )
    grau_mutacao: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Grau de mutação para o algoritmo genético (0.00 a 10.00).",
    )
    populacao_apenas_aleatoria: int = Field(
        default=1,
        ge=0,
        le=1,
        description="Indica se a população inicial deve ser gerada apenas de forma aleatória (1=sim, 0=não).",
    )
    tamanho_populacao: int = Field(
        default=100,
        ge=1,
        le=10_000,
        description="Tamanho da população para o algoritmo genético.",
    )
    tamanho_elite: int = Field(
        ...,
        ge=1,
        description="Número de indivíduos que compõem a elite (mínimo 1, máximo tamanho_populacao - 1).",
    )

    tipo_selecao: Literal["truncamento", "torneio"] = Field(
        default="truncamento",
        description=(
            "Método de seleção dos pais: "
            "'truncamento' = preserva os N melhores (padrão); "
            "'torneio' = sorteia k candidatos e escolhe o melhor (menos pressão seletiva)."
        ),
    )
    tipo_crossover: Literal["ox", "erx"] = Field(
        default="ox",
        description=(
            "Operador de crossover: "
            "'ox' = Order Crossover, preserva ordem relativa (padrão); "
            "'erx' = Edge Recombination Crossover, preserva arestas — melhor para TSP puro."
        ),
    )
    tipo_mutacao: Literal["swap", "inversao", "ambos", "or_opt"] = Field(
        default="ambos",
        description=(
            "Operador de mutação: "
            "'swap' = troca dois vizinhos adjacentes; "
            "'inversao' = inverte segmento; "
            "'ambos' = swap + inversão (padrão); "
            "'or_opt' = remove segmento de 1-3 cidades e reinsere em outra posição."
        ),
    )
    usar_2opt: int = Field(
        default=0,
        ge=0,
        le=1,
        description=(
            "Aplica busca local 2-opt a cada filho gerado (1=sim, 0=não). "
            "Aumenta qualidade da rota mas eleva significativamente o tempo de execução. "
            "Recomenda-se reduzir tamanho_populacao e epocas ao ativar."
        ),
    )
    tipo_inicializacao: Literal["aleatoria", "vizinho_mais_proximo"] = Field(
        default="aleatoria",
        description=(
            "Estratégia de geração da população inicial: "
            "'aleatoria' = rotas embaralhadas aleatoriamente (padrão); "
            "'vizinho_mais_proximo' = inclui um indivíduo gerado pela heurística gulosa."
        ),
    )
    usar_parada_antecipada: int = Field(
        default=0,
        ge=0,
        le=1,
        description=(
            "Encerra o algoritmo antes de completar todas as épocas caso a aptidão não "
            "melhore por `paciencia_parada_antecipada` épocas seguidas (1=sim, 0=não). "
            "Só tem efeito quando elitismo=1 — sem elitismo a aptidão pode oscilar "
            "legitimamente entre gerações, tornando a ausência de melhora um sinal não "
            "confiável para encerrar a execução."
        ),
    )
    paciencia_parada_antecipada: int = Field(
        default=30,
        ge=1,
        le=100_000,
        description=(
            "Número de épocas consecutivas sem melhora na aptidão toleradas antes de "
            "encerrar antecipadamente. Só é considerado quando usar_parada_antecipada=1 "
            "e elitismo=1."
        ),
    )

    @model_validator(mode="after")
    def validar_tamanho_elite(self) -> "RotasRequest":
        if self.tamanho_elite >= self.tamanho_populacao:
            raise ValueError(
                f"tamanho_elite ({self.tamanho_elite}) deve ser menor que "
                f"tamanho_populacao ({self.tamanho_populacao})."
            )
        return self
