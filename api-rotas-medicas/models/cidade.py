import math
from typing import Optional

from models.produto import Produto


class Cidade:
    """
    Representa uma cidade no Problema do Caixeiro Viajante (TSP).

    Atributos
    ---------
    cod_ibge   : int        — Código IBGE da cidade (ex.: 3550308 para São Paulo)
    nome       : str        — nome da cidade
    uf         : str        — sigla do estado (ex.: "SP", "RJ")
    latitude   : float      — latitude geográfica em graus decimais
    longitude  : float      — longitude geográfica em graus decimais
    regiao_tradicional : str | None — região tradicional à qual a cidade pertence
    produto    : Produto | produto a ser entregue na cidade
    """

    RAIO_TERRA_KM: float = 6371.0  # raio médio da Terra em KM

    def __init__(
        self,
        cod_ibge: int,
        nome: str,
        uf: str,
        latitude: float,
        longitude: float,
        regiao_tradicional: str | None,
        produto: Produto | None = None,
    ) -> None:
        """
        Parâmetros
        ----------
        cod_ibge   : int        — código IBGE da cidade (ex.: 3550308 para São Paulo)
        nome       : str        — nome da cidade (ex.: "São Paulo")
        uf         : str        — sigla do estado com 2 letras maiúsculas (ex.: "SP")
        latitude   : float      — latitude em graus decimais (negativo = Sul)
        longitude  : float      — longitude em graus decimais (negativo = Oeste)
        regiao_tradicional : str | None — região tradicional à qual a cidade pertence
        produto    : Produto | None — produto a ser entregue na cidade
        """
        
        self.cod_ibge: int          = cod_ibge
        self.nome: str             = nome
        self.uf: str               = uf.upper()
        self.latitude: float       = latitude
        self.longitude: float      = longitude
        self.regiao_tradicional: str | None = regiao_tradicional
        self.produto: Produto | None = produto

    # ------------------------------------------------------------------
    # Cálculo de distância
    # ------------------------------------------------------------------

    def distancia_para(self, outra: "Cidade") -> float:
        """
        Calcula a distância geodésica (Haversine) entre esta cidade e outra,
        em quilômetros.

        A fórmula de Haversine leva em conta a curvatura da Terra, sendo mais
        precisa que a distância euclidiana para coordenadas geográficas reais.

        Parâmetros
        ----------
        outra : Cidade — cidade de destino

        Retorna
        -------
        float — distância em KM
        """
        lat1 = math.radians(self.latitude)
        lat2 = math.radians(outra.latitude)
        dlat = math.radians(outra.latitude - self.latitude)
        dlon = math.radians(outra.longitude - self.longitude)

        a = (math.sin(dlat / 2) ** 2
             + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)

        return self.RAIO_TERRA_KM * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # ------------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------------

    def __eq__(self, outra: object) -> bool:
        """Duas cidades são iguais se tiverem o mesmo código IBGE."""
        return isinstance(outra, Cidade) and self.cod_ibge == outra.cod_ibge

    def __hash__(self) -> int:
        """Permite usar Cidade em sets e como chave de dicionário."""
        return hash(self.cod_ibge)




