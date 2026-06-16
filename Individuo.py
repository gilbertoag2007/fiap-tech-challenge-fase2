import random
from typing import Optional
from cidade import Cidade


class Individuo:
    """
    Representa um indivíduo (solução candidata) para o problema do Caixeiro
    Viajante (TSP) resolvido via Algoritmos Genéticos.
    
    Atributos
    ---------

    cromossomo : list[Cidade]
        Permutação das cidades definindo uma rota e ordem de visita.
       
    """

    def __init__(self, cidades: list[Cidade]) -> None:
        self.cromossomo: list[Cidade] = self.gerar_cromossomo_aleatorio(cidades)

    # ------------------------------------------------------------------
    # Inicialização
    # ------------------------------------------------------------------

    def gerar_cromossomo_aleatorio(self, cidades: list[Cidade]) -> list[Cidade]:
        """Cria uma permutação aleatória da lista de cidades."""
        rota = list(cidades)
        random.shuffle(rota)
        return rota


    def calcular_aptidao(self) -> float:
        """
        Calcula e armazena a distância total da rota usando Haversine,
        chamando diretamente cidade.distancia_para(outra).
        O retorno é a distancia total de todas as cidades da solução (Individuo).

        -------
        float — distância total em KM.
        """
        distancia_total = 0.0
        n = len(self.cromossomo)

        for i in range(n):
            origem  = self.cromossomo[i]
            destino = self.cromossomo[(i + 1) % n]  # % n fecha o ciclo
            distancia_total += origem.distancia_para(destino)

        self.aptidao = distancia_total
        return self.aptidao


    # ------------------------------------------------------------------
    # Validação
    # ------------------------------------------------------------------

    def is_valido(self) -> bool:
        """
        Verifica se o cromossomo é uma permutação válida:
        - Retorna True ou False indicando se existem cidades repetidas no cromossomo.
        """
        ids_cidades = {c.id for c in self.cromossomo}
        tem_duplicata = len(ids_cidades) != len(set(ids_cidades))
       
        return tem_duplicata

    # ------------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------------

    def copiar(self) -> "Individuo":
        """Retorna uma cópia independente deste indivíduo."""
        copia = Individuo(self.cidades)
        
        return copia

    def rota_nomes(self) -> list[str]:
        """Retorna a sequência de nomes das cidades na ordem da rota."""
        return [c.nome for c in self.cromossomo]

