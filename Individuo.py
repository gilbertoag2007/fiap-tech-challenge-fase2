from cidade import Cidade


class Individuo:
    """
    Representa um indivíduo (solução candidata) para o problema do Caixeiro
    Viajante (TSP) resolvido via Algoritmos Genéticos.

    Parâmetros
    ----------
    partida : Cidade
        Cidade de partida — deve ser o primeiro e o último elemento do cromossomo.
    cromossomo : list[Cidade]
        Rota completa já construída, incluindo a cidade de partida no início e no fim.

    Atributos
    ---------
    cromossomo : list[Cidade]
        Sequência de cidades que define a rota circular.
    """

    def __init__(self, partida: Cidade, cromossomo: list[Cidade]) -> None:
        self.partida = partida
        self.cromossomo: list[Cidade] = cromossomo


    # Penalidade adicionada à aptidão por cada par (insumo antes de vacina) na rota.
    # Valor alto o suficiente para que qualquer rota com violação seja pior
    # do que qualquer rota válida, independentemente da distância.
    _PENALIDADE_POR_VIOLACAO: float = 10_000.0

    def calcular_aptidao(self) -> float:
        """
        Calcula a aptidão do indivíduo como:
            aptidao = distancia_total + penalidade_prioridade

        A penalidade é aplicada quando cidades de menor prioridade ("insumo")
        aparecem antes de cidades de maior prioridade ("vacina") na rota.
        Cada par fora de ordem adiciona _PENALIDADE_POR_VIOLACAO à aptidão.

        Atributos definidos após a chamada
        ------------------------------------
        distancia : float — distância real percorrida em KM (sem penalidade)
        aptidao   : float — valor usado pelo AG para comparar indivíduos

        Retorna
        -------
        float — aptidão total (menor = melhor).
        """
        distancia_total = 0.0
        n = len(self.cromossomo)
        for i in range(n - 1):
            distancia_total += self.cromossomo[i].distancia_para(self.cromossomo[i + 1])

        self.distancia = distancia_total
        self.aptidao   = distancia_total + self._penalidade_prioridade()
        return self.aptidao

    def _penalidade_prioridade(self) -> float:
        """Conta pares (insumo, vacina) fora de ordem e retorna a penalidade total."""
        cidades_rota = self.cromossomo[1:-1] # sem a cidade de partida e chegada
        violacoes = sum(
            1
            for i, a in enumerate(cidades_rota)
            for b in cidades_rota[i + 1:]
            if a.produto.prioridade > b.produto.prioridade
        )
        return violacoes * self._PENALIDADE_POR_VIOLACAO


    # ------------------------------------------------------------------
    # Validação
    # ------------------------------------------------------------------

    def is_valido(self) -> bool:
        """
        Verifica se o cromossomo é uma permutação válida:
        - Primeira e última cidade devem ser a cidade de partida.
        - As cidades internas não podem ter duplicatas nem conter a partida.
        - Retorna True se válido, False caso contrário.
        """
        ids = [c.id for c in self.cromossomo]
        if not ids or ids[0] != self.partida.id or ids[-1] != self.partida.id:
            return False
        inner_ids = ids[1:-1]
        return len(inner_ids) == len(set(inner_ids)) and self.partida.id not in set(inner_ids)

    # ------------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------------

    def copiar(self) -> "Individuo":
        """Retorna uma cópia independente deste indivíduo."""
        return Individuo(self.partida, list(self.cromossomo))

    def rota_nomes(self) -> list[str]:
        """Retorna a sequência de nomes das cidades na ordem da rota."""
        return [c.nome for c in self.cromossomo]

