from models.cidade import Cidade


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
        Sequência ordenada de cidades que define a rota circular.
    """

    def __init__(self, partida: Cidade, cromossomo: list[Cidade]) -> None:
        self.partida = partida
        self.cromossomo: list[Cidade] = cromossomo


    # Bonificação subtraída da aptidão por cidade de prioridade 1 ("vacina"),
    # ponderada pela posição na rota (quanto mais cedo, maior o bônus).
    # Ordem de grandeza escolhida para ficar próxima da escala de uma única
    # perna do trajeto (dezenas a centenas de KM): grande o suficiente para
    # orientar a seleção do AG em direção à antecipação de prioridades, mas
    # baixa o suficiente para não sobrepor economias reais de distância —
    # ao contrário da extinta _PENALIDADE_POR_VIOLACAO (10_000.0), que era
    # deliberadamente dominante para forçar uma restrição quase rígida.
    _BONIFICACAO_POR_ANTECIPACAO: float = 100.0

    def calcular_aptidao(self) -> float:
        """
        Calcula a aptidão do indivíduo como:
            aptidao = distancia_total - bonificacao_prioridade

        A bonificação recompensa cidades de maior prioridade ("vacina") por
        ocuparem posições mais cedo na rota: cada uma contribui com
        (posicoes_restantes * _BONIFICACAO_POR_ANTECIPACAO), de modo que
        quanto mais cedo a cidade aparecer, maior o bônus.

        Atributos definidos após a chamada
        ------------------------------------
        distancia : float — distância real percorrida em KM (sem bonificação)
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
        self.aptidao   = distancia_total - self._bonificacao_prioridade()
        return self.aptidao

    def _bonificacao_prioridade(self) -> float:
        """Bonifica cidades de prioridade 1 por ocuparem posições mais cedo na rota."""
        cidades_rota = self.cromossomo[1:-1]  # sem a cidade de partida e chegada
        n = len(cidades_rota)
        return sum(
            (n - i) * self._BONIFICACAO_POR_ANTECIPACAO
            for i, c in enumerate(cidades_rota)
            if c.produto.prioridade == 1
        )


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
        ids = [c.cod_ibge for c in self.cromossomo]
        if not ids or ids[0] != self.partida.cod_ibge or ids[-1] != self.partida.cod_ibge:
            return False
        inner_ids = ids[1:-1]
        return len(inner_ids) == len(set(inner_ids)) and self.partida.cod_ibge not in set(inner_ids)

    # ------------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------------

    def copiar(self) -> "Individuo":
        """Retorna uma cópia independente deste indivíduo."""
        return Individuo(self.partida, list(self.cromossomo))

    def rota_nomes(self) -> list[str]:
        """Retorna a sequência de nomes das cidades na ordem da rota."""
        return [c.nome for c in self.cromossomo]

