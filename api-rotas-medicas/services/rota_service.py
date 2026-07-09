import random
from typing import Any

from models.Individuo import Individuo
from services.cidade_service import cidade_service
from services.llm_service import LLMService
from services import algoritmos_geneticos as ag


class RotaService:

    # ---------------------------------------------------------------------------
    # Ponto de entrada do service
    # ---------------------------------------------------------------------------

    def calcular_rota(
        self,
        mensagem: str,
        epocas: int,
        elitismo: int,
        grau_mutacao: float,
        populacao_apenas_aleatoria: int,
        tamanho_populacao: int,
        tamanho_elite: int,
        capacidade_veiculo_kg: float | None = None,
        tipo_selecao: str = "truncamento",
        tipo_crossover: str = "ox",
        tipo_mutacao: str = "ambos",
        usar_2opt: int = 0,
        tipo_inicializacao: str = "aleatoria",
        usar_parada_antecipada: int = 0,
        paciencia_parada_antecipada: int = 30,
    ) -> dict[str, Any]:
        """
        Executa o algoritmo genético e retorna a rota otimizada como GeoJSON FeatureCollection.

        Parâmetros
        ----------
        mensagem : str
            Descrição textual da rota a ser otimizada (interpretada via ChatGPT).
        epocas : int
            Número de gerações do algoritmo genético.
        elitismo : int
            1 = preserva os melhores indivíduos na próxima geração, 0 = não preserva.
        grau_mutacao : float
            Taxa de mutação em percentual (0.00 a 10.00). Convertido para 0.0–1.0 internamente.
        capacidade_veiculo_kg : float | None
            Capacidade máxima opcional do veículo em kg. Quando informada, excesso de
            carga gera penalidade na aptidão.
        populacao_apenas_aleatoria : int
            Reservado para extensões futuras (não altera o comportamento atual).
        tamanho_populacao : int
            Número de indivíduos na população.
        tamanho_elite : int
            Número de indivíduos preservados pelo elitismo a cada geração.
        tipo_selecao : str
            'truncamento' (padrão) ou 'torneio'.
        tipo_crossover : str
            'ox' (padrão) ou 'erx'.
        tipo_mutacao : str
            'swap', 'inversao', 'ambos' (padrão) ou 'or_opt'.
        usar_2opt : int
            1 = aplica busca local 2-opt em cada filho gerado. Aumenta qualidade
            mas eleva o custo computacional — recomenda-se reduzir a população e
            as épocas ao ativar.
        tipo_inicializacao : str
            'aleatoria' (padrão) ou 'vizinho_mais_proximo'.
        usar_parada_antecipada : int
            1 = encerra o algoritmo antes de completar todas as épocas caso a aptidão não
            melhore por `paciencia_parada_antecipada` épocas seguidas. Só tem efeito
            quando elitismo=1 (sem elitismo a aptidão pode oscilar legitimamente entre
            gerações, tornando a ausência de melhora um sinal não confiável).
        paciencia_parada_antecipada : int
            Número de épocas consecutivas sem melhora toleradas antes de encerrar
            antecipadamente. Só é considerado quando usar_parada_antecipada=1 e elitismo=1.

        Retorna
        -------
        dict — GeoJSON FeatureCollection com a rota otimizada.
        """
        pares = LLMService().interpretar_mensagem(mensagem)

        if not pares:
            raise ValueError("Nenhuma cidade encontrada com os parâmentros informados.")

        lista_cidades = cidade_service.montar_cidades_com_produtos(pares)

        if len(lista_cidades) < 2:
            raise ValueError("São necessárias ao menos 2 cidades para calcular uma rota.")

        partida = lista_cidades[0]
        probabilidade_mutacao = grau_mutacao / 100.0

        # Parada antecipada só é confiável com elitismo=1 (garante que a aptidão nunca
        # piora entre épocas); sem elitismo, "sem melhora" pode ser apenas oscilação normal.
        parada_antecipada_ativa = usar_parada_antecipada == 1 and elitismo == 1

        print(
            f"[RotaService] {len(lista_cidades)} cidades | {epocas} épocas | "
            f"população={tamanho_populacao} | elite={tamanho_elite} | "
            f"mutação={probabilidade_mutacao:.4f} | elitismo={elitismo} | "
            f"capacidade_kg={capacidade_veiculo_kg if capacidade_veiculo_kg is not None else 'sem limite'} | "
            f"seleção={tipo_selecao} | crossover={tipo_crossover} | "
            f"mutação_op={tipo_mutacao} | 2opt={usar_2opt} | init={tipo_inicializacao} | "
            f"parada_antecipada={'ativa (paciência=' + str(paciencia_parada_antecipada) + ')' if parada_antecipada_ativa else 'inativa'}"
        )

        # --- Inicialização da população ---
        if tipo_inicializacao == "vizinho_mais_proximo":
            individuo_nn = ag.gerar_individuo_vizinho_mais_proximo(
                partida, lista_cidades, capacidade_veiculo_kg
            )
            populacao = ag.gerar_populacao_aleatoria(
                tamanho_populacao, partida, lista_cidades,
                melhores_individuos=[individuo_nn],
                capacidade_veiculo_kg=capacidade_veiculo_kg,
            )
        else:
            populacao = ag.gerar_populacao_aleatoria(
                tamanho_populacao, partida, lista_cidades,
                capacidade_veiculo_kg=capacidade_veiculo_kg,
            )

        # --- Loop evolucionário ---
        historico_evolucao: list[dict[str, Any]] = []
        intervalo_amostra = self._calcular_intervalo_amostra(
            epocas, parada_antecipada_ativa, paciencia_parada_antecipada
        )

        melhor_aptidao_referencia: float | None = None
        epocas_sem_melhora = 0
        epocas_executadas = 0
        parou_antecipadamente = False
        total_avaliacoes_aptidao = 0

        for epoca in range(epocas):
            epocas_executadas = epoca + 1

            # Seleção dos pais para cruzamento
            if tipo_selecao == "torneio":
                melhores = ag.selecionar_por_torneio(populacao, tamanho_elite)
            else:
                melhores = ag.seleciona_melhores_individuos(populacao, tamanho_elite)

            # Elitismo: preserva sempre os verdadeiros melhores indivíduos da população,
            # independente do método usado para selecionar os pais. O torneio é estocástico
            # e pode não sortear o melhor indivíduo entre seus vencedores — usar `melhores`
            # diretamente nesse caso deixaria o melhor indivíduo se perder entre gerações.
            if elitismo == 1:
                elite = (
                    ag.seleciona_melhores_individuos(populacao, tamanho_elite)
                    if tipo_selecao == "torneio"
                    else melhores
                )
                nova_populacao: list[Individuo] = list(elite)
            else:
                nova_populacao = []

            while len(nova_populacao) < tamanho_populacao:
                parent1, parent2 = random.choices(melhores, k=2)

                # Crossover
                if tipo_crossover == "erx":
                    filho = ag.cruzamento_erx(parent1, parent2, partida)
                else:
                    filho = ag.cruzamento_ox(parent1, parent2, partida)

                # Mutação
                if tipo_mutacao == "swap":
                    filho = ag.mutacao_simples(filho, probabilidade_mutacao)
                elif tipo_mutacao == "inversao":
                    filho = ag.mutacao_inversao(filho, probabilidade_mutacao)
                elif tipo_mutacao == "or_opt":
                    filho = ag.mutacao_or_opt(filho, probabilidade_mutacao)
                else:  # "ambos" — comportamento padrão original
                    filho = ag.mutacao_simples(filho, probabilidade_mutacao)
                    filho = ag.mutacao_inversao(filho, probabilidade_mutacao)

                # Busca local 2-opt (opcional)
                if usar_2opt == 1:
                    filho = ag.busca_local_2opt(filho)

                nova_populacao.append(filho)
                total_avaliacoes_aptidao += 1

            populacao = nova_populacao

            # Só recalcula o melhor indivíduo fora do ponto de amostragem quando a
            # parada antecipada está ativa — evita custo extra nos demais casos.
            eh_ponto_amostra = (epoca + 1) % intervalo_amostra == 0
            melhor_epoca = None
            if eh_ponto_amostra or parada_antecipada_ativa:
                melhor_epoca = ag.seleciona_melhores_individuos(populacao, 1)[0]

            if eh_ponto_amostra:
                stats_populacao = ag.calcular_estatisticas_populacao(populacao)
                historico_evolucao.append({
                    "epoca": epoca + 1,
                    "distancia_km": round(melhor_epoca.distancia, 2),
                    "aptidao": round(melhor_epoca.aptidao, 2),
                    "aptidao_media": round(stats_populacao["aptidao_media"], 2),
                    "aptidao_pior": round(stats_populacao["aptidao_pior"], 2),
                    "diversidade": round(stats_populacao["diversidade"], 4),
                })
                print(
                    f"[RotaService] época {epoca + 1}/{epocas} | "
                    f"melhor distância={melhor_epoca.distancia:.2f} km | "
                    f"aptidão (melhor/média/pior)={melhor_epoca.aptidao:.2f}/"
                    f"{stats_populacao['aptidao_media']:.2f}/{stats_populacao['aptidao_pior']:.2f} | "
                    f"diversidade={stats_populacao['diversidade']:.2%}"
                )

            if parada_antecipada_ativa:
                if melhor_aptidao_referencia is None or melhor_epoca.aptidao < melhor_aptidao_referencia - 1e-9:
                    melhor_aptidao_referencia = melhor_epoca.aptidao
                    epocas_sem_melhora = 0
                else:
                    epocas_sem_melhora += 1

                if epocas_sem_melhora >= paciencia_parada_antecipada:
                    parou_antecipadamente = True
                    print(
                        f"[RotaService] Parada antecipada na época {epoca + 1}/{epocas} — "
                        f"sem melhora por {paciencia_parada_antecipada} épocas seguidas."
                    )
                    break

        melhor = ag.seleciona_melhores_individuos(populacao, 1)[0]
        rota_valida = melhor.is_valido()
        diagnostico_prioridade = self._diagnostico_prioridade(melhor)
        diagnostico_capacidade = self._diagnostico_capacidade(melhor, capacidade_veiculo_kg)
        print(
            f"[RotaService] Rota final: {melhor.rota_nomes()} | "
            f"distância={melhor.distancia:.2f} km | aptidão={melhor.aptidao:.2f} | "
            f"válida={rota_valida} | {diagnostico_prioridade} | {diagnostico_capacidade}"
        )

        return {
            "type": "FeatureCollection",
            "features": self._individuo_para_features(melhor),
            "km_total": round(melhor.distancia, 2),
            "aptidao_final": round(melhor.aptidao, 2),
            "total_cidades": len(melhor.cromossomo) - 1,
            "historico_evolucao": historico_evolucao,
            "epocas_executadas": epocas_executadas,
            "parou_antecipadamente": parou_antecipadamente,
            "total_avaliacoes_aptidao": total_avaliacoes_aptidao,
            "rota_valida": rota_valida,
            **diagnostico_prioridade,
            **diagnostico_capacidade,
        }

    # ---------------------------------------------------------------------------
    # Auxiliar: intervalo de amostragem do historico_evolucao
    # ---------------------------------------------------------------------------

    def _calcular_intervalo_amostra(
        self, epocas: int, parada_antecipada_ativa: bool, paciencia_parada_antecipada: int
    ) -> int:
        """
        Define a cada quantas épocas um ponto é registrado em `historico_evolucao`.

        Sem parada antecipada, a execução sempre completa `epocas` gerações, então
        amostrar a 10% do total garante ~10 pontos bem distribuídos.

        Com parada antecipada ativa, a execução pode encerrar bem antes de `epocas`
        — amostrar a 10% de `epocas` arriscaria produzir 0 ou 1 ponto (insuficiente
        para o frontend desenhar uma linha de evolução) sempre que a parada disparar
        cedo, o que é comum. Nesse caso, a amostragem usa uma fração da paciência
        (independente de `epocas`), garantindo ao menos ~3 pontos dentro da própria
        janela de estagnação que antecede qualquer parada.

        Parâmetros
        ----------
        epocas : int
        parada_antecipada_ativa : bool
        paciencia_parada_antecipada : int

        Retorna
        -------
        int — intervalo em número de épocas entre cada ponto amostrado.
        """
        if parada_antecipada_ativa:
            return max(1, paciencia_parada_antecipada // 3)
        return max(1, epocas // 10)

    # ---------------------------------------------------------------------------
    # Auxiliar: conversão do melhor Individuo para features GeoJSON
    # ---------------------------------------------------------------------------

    def _individuo_para_features(self, melhor: Individuo) -> list[dict[str, Any]]:
        """
        Converte o cromossomo do melhor indivíduo em uma lista de GeoJSON Features.

        Cada cidade da rota (excluindo o retorno à partida) gera uma Feature do tipo
        Point com as propriedades de visita, produto e prioridade.

        Parâmetros
        ----------
        melhor : Individuo
            Melhor indivíduo encontrado após calcular_aptidao().

        Retorna
        -------
        list[dict] — lista de GeoJSON Features ordenadas pela ordem de visita.
        """
        features: list[dict[str, Any]] = []
        for ordem, cidade in enumerate(melhor.cromossomo[:-1], start=1):
            features.append(
                {
                    "type": "Feature",
                    "properties": {
                        "ordem_visita": str(ordem),
                        "cidade": cidade.nome,
                        "regiao_tradicional": cidade.regiao_tradicional,
                        "uf": cidade.uf,
                        "produto": cidade.produto.nome if cidade.produto else None,
                        "prioridade": str(cidade.produto.prioridade) if cidade.produto else None,
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [cidade.longitude, cidade.latitude],  # GeoJSON = [lon, lat]
                    },
                }
            )
        return features

    # ---------------------------------------------------------------------------
    # Auxiliar: diagnóstico da efetividade da bonificação de prioridade
    # ---------------------------------------------------------------------------

    def _diagnostico_prioridade(self, melhor: Individuo) -> dict[str, Any]:
        """
        Mede se as cidades de prioridade 1 (alta urgência) de fato ficaram
        posicionadas mais cedo na rota final — evidência de que a bonificação
        de `Individuo._bonificacao_prioridade` está cumprindo seu propósito,
        não apenas otimizando distância. A posição média de prioridade 2
        também é calculada, como contraponto: como só prioridade 1 recebe
        bônus posicional na aptidão (prioridade 2 compete apenas pela
        distância, sem incentivo de posição), o contraste entre as duas
        médias evidencia melhor o efeito da bonificação do que olhar cada
        uma isoladamente.

        Usa a mesma numeração de `ordem_visita` de `_individuo_para_features`
        (a partida ocupa a posição 1) para que o resultado seja diretamente
        comparável à lista de cidades exibida ao usuário.

        Parâmetros
        ----------
        melhor : Individuo
            Melhor indivíduo encontrado após calcular_aptidao().

        Retorna
        -------
        dict com, para cada prioridade (1 e 2):
        - "cidades_prioridade_N": int — quantidade de cidades daquela prioridade na rota.
        - "posicao_media_prioridade_N_percentual": float | None — posição média
          (ordem_visita) das cidades daquela prioridade, normalizada em % do total
          de cidades da rota (0% = logo no início, 100% = no fim). None se não
          houver cidades daquela prioridade na rota.
        """
        total_cidades = len(melhor.cromossomo) - 1
        posicoes_por_prioridade: dict[int, list[int]] = {1: [], 2: []}
        for ordem, cidade in enumerate(melhor.cromossomo[:-1], start=1):
            if cidade.produto and cidade.produto.prioridade in posicoes_por_prioridade:
                posicoes_por_prioridade[cidade.produto.prioridade].append(ordem)

        def _posicao_media_percentual(posicoes: list[int]) -> float | None:
            if not posicoes or total_cidades == 0:
                return None
            posicao_media = sum(posicoes) / len(posicoes)
            return round((posicao_media / total_cidades) * 100, 1)

        return {
            "cidades_prioridade_1": len(posicoes_por_prioridade[1]),
            "posicao_media_prioridade_1_percentual": _posicao_media_percentual(posicoes_por_prioridade[1]),
            "cidades_prioridade_2": len(posicoes_por_prioridade[2]),
            "posicao_media_prioridade_2_percentual": _posicao_media_percentual(posicoes_por_prioridade[2]),
        }

    # ---------------------------------------------------------------------------
    # Auxiliar: diagnóstico de capacidade de carga
    # ---------------------------------------------------------------------------

    def _diagnostico_capacidade(
        self, melhor: Individuo, capacidade_veiculo_kg: float | None
    ) -> dict[str, Any]:
        carga_total_kg = round(melhor.calcular_carga_total_kg(), 2)
        excesso_carga_kg = (
            round(max(0.0, carga_total_kg - capacidade_veiculo_kg), 2)
            if capacidade_veiculo_kg is not None
            else 0.0
        )
        uso_capacidade_percentual = (
            round((carga_total_kg / capacidade_veiculo_kg) * 100, 1)
            if capacidade_veiculo_kg is not None
            else None
        )
        return {
            "carga_total_kg": carga_total_kg,
            "capacidade_veiculo_kg": capacidade_veiculo_kg,
            "excesso_carga_kg": excesso_carga_kg,
            "capacidade_excedida": excesso_carga_kg > 0,
            "uso_capacidade_percentual": uso_capacidade_percentual,
        }
