from pydantic import BaseModel, Field, model_validator


class RotasRequest(BaseModel):
    """
    Schema para a requisição de rotas médicas.
    """
    mensagem: str = Field(
        ...,
        min_length=20,
        max_length=200,
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

    @model_validator(mode="after")
    def validar_tamanho_elite(self) -> "RotasRequest":
        if self.tamanho_elite >= self.tamanho_populacao:
            raise ValueError(
                f"tamanho_elite ({self.tamanho_elite}) deve ser menor que "
                f"tamanho_populacao ({self.tamanho_populacao})."
            )
        return self