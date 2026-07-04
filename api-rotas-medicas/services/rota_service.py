import random
from typing import Any

from models.individuo import Individuo
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
            f"seleção={tipo_selecao} | crossover={tipo_crossover} | "
            f"mutação_op={tipo_mutacao} | 2opt={usar_2opt} | init={tipo_inicializacao} | "
            f"parada_antecipada={'ativa (paciência=' + str(paciencia_parada_antecipada) + ')' if parada_antecipada_ativa else 'inativa'}"
        )

        # --- Inicialização da população ---
        if tipo_inicializacao == "vizinho_mais_proximo":
            individuo_nn = ag.gerar_individuo_vizinho_mais_proximo(partida, lista_cidades)
            populacao = ag.gerar_populacao_aleatoria(
                tamanho_populacao, partida, lista_cidades,
                melhores_individuos=[individuo_nn],
            )
        else:
            populacao = ag.gerar_populacao_aleatoria(tamanho_populacao, partida, lista_cidades)

        # --- Loop evolucionário ---
        historico_evolucao: list[dict[str, Any]] = []
        intervalo_amostra = max(1, epocas // 10)

        melhor_aptidao_referencia: float | None = None
        epocas_sem_melhora = 0
        epocas_executadas = 0
        parou_antecipadamente = False

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

            populacao = nova_populacao

            # Só recalcula o melhor indivíduo fora do ponto de amostragem quando a
            # parada antecipada está ativa — evita custo extra nos demais casos.
            eh_ponto_amostra = (epoca + 1) % intervalo_amostra == 0
            melhor_epoca = None
            if eh_ponto_amostra or parada_antecipada_ativa:
                melhor_epoca = ag.seleciona_melhores_individuos(populacao, 1)[0]

            if eh_ponto_amostra:
                historico_evolucao.append({
                    "epoca": epoca + 1,
                    "distancia_km": round(melhor_epoca.distancia, 2),
                    "aptidao": round(melhor_epoca.aptidao, 2),
                })
                print(
                    f"[RotaService] época {epoca + 1}/{epocas} | "
                    f"melhor distância={melhor_epoca.distancia:.2f} km | "
                    f"aptidão={melhor_epoca.aptidao:.2f}"
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
        print(
            f"[RotaService] Rota final: {melhor.rota_nomes()} | "
            f"distância={melhor.distancia:.2f} km | aptidão={melhor.aptidao:.2f}"
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
        }

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
