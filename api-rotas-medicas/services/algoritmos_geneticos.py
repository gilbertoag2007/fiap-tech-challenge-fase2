"""
Operadores genéticos do TSP: inicialização de população, seleção de pais,
crossover, mutação e busca local — usados por RotaService para montar o
laço evolutivo configurável (seleção, crossover, mutação, 2-opt e
inicialização são escolhidos em tempo de execução via RotasRequest).

Convenção de aptidão: menor `individuo.aptidao` é sempre melhor (ver
Individuo.calcular_aptidao) — todo operador de seleção/comparação aqui
ordena ou escolhe por valor mínimo, nunca máximo.
"""

import copy
import random
from math import factorial
from typing import Optional

from models.Individuo import Individuo
from models.cidade import Cidade


def gerar_individuo_aleatorio(
    partida: Cidade,
    cidades: list[Cidade],
    capacidade_veiculo_kg: float | None = None,
) -> Individuo:
    """
    Cria um indivíduo com cromossomo aleatorio.

    A cidade de partida é fixada na primeira e na última posição (rota circular).
    As demais cidades são embaralhadas aleatoriamente entre essas posições.

    Parâmetros
    ----------
    partida : Cidade
        Cidade de partida e chegada da rota.
    cidades : list[Cidade]
        Lista completa de cidades a serem visitadas (incluindo a partida).

    Retorna
    -------
    Individuo — novo indivíduo com cromossomo [partida, ..., partida].
    """
    outras = [c for c in cidades if c.cod_ibge != partida.cod_ibge]
    random.shuffle(outras)
    return Individuo(partida, [partida] + outras + [partida], capacidade_veiculo_kg)


def seleciona_melhores_individuos(populacao: list[Individuo], quantidade: int) -> list[Individuo]:
    """Seleciona (por truncamento) os `quantidade` indivíduos com menor aptidão da população.

    Aptidão aqui já inclui a bonificação de prioridade (ver Individuo.calcular_aptidao),
    portanto não corresponde necessariamente à menor distância percorrida — apenas ao
    menor valor de `aptidao`.
    """
    return sorted(populacao, key=lambda x: x.calcular_aptidao())[:quantidade]


def gerar_populacao_aleatoria(
    quantidade: int, 
    partida: Cidade, 
    cidades: list[Cidade],
    melhores_individuos: Optional[list[Individuo]] = None,
    capacidade_veiculo_kg: float | None = None,
) -> list[Individuo]:
    """
    Gera uma população inicial de indivíduos com rotas aleatórias e únicas.
 
    Parâmetros
    ----------
    quantidade : int
        Número total de indivíduos a serem gerados na população.
    partida : Cidade
        Cidade de partida que será sempre o primeiro elemento de cada cromossomo.
    cidades : list[Cidade]
        Lista de todas as cidades a serem visitadas.
    melhores_individuos : Optional[list[Individuo]], default=None
        Lista opcional de melhores indivíduos de uma população anterior.
        Se fornecida, esses indivíduos serão incluídos na nova população,
        e o número de novos indivíduos gerados será: quantidade - len(melhores_individuos).
 
    Retorna
    -------
    list[Individuo] — população gerada com 'quantidade' indivíduos únicos,
                      cada um começando e terminando obrigatoriamente com a cidade de partida.

    Notas
    -----
    - Cada indivíduo começará e terminará obrigatoriamente com a cidade de partida (rota circular).
    - Indivíduos duplicados são evitados através da verificação de cromossomos únicos.
    - Se melhores_individuos for fornecido, eles serão incluídos na população.
    - Se não conseguir gerar indivíduos suficientes, lança uma exceção.
    
    Raises
    ------
    ValueError
        Se a lista de cidades estiver vazia, se a partida não estiver na lista,
        se melhores_individuos contiver indivíduos que não começam com partida,
        ou se não conseguir gerar o número solicitado de indivíduos únicos.
    
    Exemplos
    --------
    >>> # Exemplo 1: Gerar população inicial
    >>> cidades = [Cidade(0, "São Paulo", "SP", -23.5505, -46.6333), ...]
    >>> partida = cidades[0]
    >>> populacao1 = gerar_populacao_aleatoria(10, partida, cidades)
    >>> len(populacao1)
    10
    
    >>> # Exemplo 2: Gerar nova população com melhores da anterior
    >>> # Calcular aptidão
    >>> for ind in populacao1:
    ...     ind.calcular_aptidao()
    
    >>> # Selecionar melhores indivíduos
    >>> melhores = sorted(populacao1, key=lambda x: x.aptidao)[:3]
    >>> len(melhores)
    3
    
    >>> # Gerar nova população incluindo os 3 melhores
    >>> populacao2 = gerar_populacao_aleatoria(10, partida, cidades, 
    ...                                        melhores_individuos=melhores)
    >>> len(populacao2)
    10
    >>> # 3 indivíduos da população1 + 7 novos indivíduos aleatórios
    """
    # Validações de entrada
    if not cidades:
        raise ValueError("A lista de cidades não pode estar vazia.")

    if partida not in cidades:
        raise ValueError("A cidade de partida deve estar na lista de cidades.")

    # Limite combinatório: fixando a partida, existem (N-1)! rotas únicas possíveis.
    # Quando o número de cidades é pequeno, o parâmetro `quantidade` é ajustado
    # silenciosamente para não ultrapassar esse limite.
    max_unicas = factorial(len(cidades) - 1)
    if quantidade > max_unicas:
        quantidade = max_unicas

    populacao = []
    cromossomos_vistos = set()  # Rastreia cromossomos únicos pelos IDs

    # Processar melhores indivíduos (se fornecidos)
    if melhores_individuos:
        if not isinstance(melhores_individuos, list):
            raise ValueError("melhores_individuos deve ser uma lista de Indivíduos.")

        # Garante espaço para ao menos 1 novo indivíduo após o ajuste de quantidade
        melhores_individuos = melhores_individuos[:max(quantidade - 1, 0)]

        # Validar e incluir melhores indivíduos
        for i, individuo in enumerate(melhores_individuos):
            # Verifica se começa e termina com a partida (rota circular)
            if individuo.cromossomo[0].cod_ibge != partida.cod_ibge or individuo.cromossomo[-1].cod_ibge != partida.cod_ibge:
                raise ValueError(
                    f"O indivíduo {i+1} dos melhores não forma uma rota circular válida: "
                    f"deve começar e terminar com '{partida.nome}'. "
                    f"Rota atual: {individuo.cromossomo[0].nome} ... {individuo.cromossomo[-1].nome}."
                )

            # Registra o cromossomo como visto (pula duplicatas dentro de melhores_individuos)
            cromossomo_tupla = tuple(c.cod_ibge for c in individuo.cromossomo)
            if cromossomo_tupla not in cromossomos_vistos:
                cromossomos_vistos.add(cromossomo_tupla)
                populacao.append(individuo)

    # Calcula quantos novos indivíduos precisam ser gerados
    quantidade_novos = quantidade - len(populacao)
    tentativas = 0
    # Para espaços de busca pequenos, garante tentativas suficientes para encontrar
    # os últimos cromossomos únicos (a probabilidade de sucesso cai à medida que
    # o espaço se esgota).
    max_tentativas = max(quantidade_novos * 100, int(max_unicas) * 10)
    
    # Loop de geração com validação de unicidade
    while len(populacao) < quantidade and tentativas < max_tentativas:
        individuo = gerar_individuo_aleatorio(partida, cidades, capacidade_veiculo_kg)
        
        # Cria uma tupla de IDs para comparação eficiente
        cromossomo_tupla = tuple(c.cod_ibge for c in individuo.cromossomo)
        
        # Se cromossomo não foi visto antes, adiciona à população
        if cromossomo_tupla not in cromossomos_vistos:
            cromossomos_vistos.add(cromossomo_tupla)
            populacao.append(individuo)
        
        tentativas += 1
    
    # Valida se conseguiu gerar a quantidade solicitada
    if len(populacao) < quantidade:
        raise ValueError(
            f"Não foi possível gerar {quantidade} indivíduos únicos "
            f"após {tentativas} tentativas. Gerados apenas {len(populacao)}."
        )
    
    return populacao
 
 
# =============================================================================
# Operadores genéticos: Crossover OX
# =============================================================================

def cruzamento_ox(parent1: Individuo, parent2: Individuo, partida: Cidade) -> Individuo:
    """
    Realiza cruzamento por ordem (Order Crossover - OX) entre dois indivíduos.
    
    O método OX preserva a sequência relativa de cidades de um pai enquanto 
    insere as cidades restantes na ordem em que aparecem no outro pai.
    
    Parâmetros
    ----------
    parent1 : Individuo
        Primeiro indivíduo progenitor
    parent2 : Individuo
        Segundo indivíduo progenitor
    partida : Cidade
        Cidade de partida (será sempre o primeiro elemento do cromossomo filho)
    
    Retorna
    -------
    Individuo
        Novo indivíduo filho resultante do cruzamento
    
    Notas
    -----
    - O cromossomo filho sempre começa e termina com a cidade de partida (rota circular)
    - O cruzamento preserva a ordem relativa das cidades internas
    - Nenhuma cidade interna é duplicada no cromossomo filho

    Exemplo
    -------
    >>> # parent1.cromossomo = [SP, Campinas, Santos, Sorocaba, ..., SP]
    >>> # parent2.cromossomo = [SP, Sorocaba, Santos, Campinas, ..., SP]
    >>> # filho pode ser: [SP, Campinas, Sorocaba, Santos, ..., SP]
    """
    cromossomo_p1 = parent1.cromossomo
    cromossomo_p2 = parent2.cromossomo
    
    length = len(cromossomo_p1)
    
    # Escolher dois índices aleatórios para o segmento de cruzamento
    # (excluindo a primeira posição que é a cidade de partida)
    if length < 4:
        return Individuo(partida, list(cromossomo_p1), parent1.capacidade_veiculo_kg)

    start_index = random.randint(1, length - 3)
    end_index = random.randint(start_index + 1, length - 1)
    
    # Copiar o segmento de parent1
    segmento = cromossomo_p1[start_index:end_index]
    
    # Identificar as cidades que não estão no segmento
    cidades_no_segmento = {cidade.cod_ibge for cidade in segmento}
    
    # Preencher as posições restantes com cidades de parent2 em ordem
    cidades_restantes = [cidade for cidade in cromossomo_p2 
                        if cidade.cod_ibge not in cidades_no_segmento and cidade.cod_ibge != partida.cod_ibge]
    
    # Construir o cromossomo do filho
    filho_cromossomo = [partida]  # Começa com a partida
    
    # Adicionar cidades antes do segmento (de parent2)
    quantidade_antes = start_index - 1
    filho_cromossomo.extend(cidades_restantes[:quantidade_antes])
    
    # Adicionar o segmento
    filho_cromossomo.extend(segmento)
    
    # Adicionar cidades após o segmento (de parent2)
    filho_cromossomo.extend(cidades_restantes[quantidade_antes:])

    # Fechar a rota com a cidade de partida
    filho_cromossomo.append(partida)

    return Individuo(partida, filho_cromossomo, parent1.capacidade_veiculo_kg)


# =============================================================================
# Operadores genéticos: Mutação
# =============================================================================

def mutacao_simples(individuo: Individuo, probabilidade_mutacao: float) -> Individuo:
    """
    Realiza mutação simples por troca (swap) de duas cidades adjacentes.
    
    Com uma dada probabilidade, seleciona duas posições adjacentes no cromossomo
    e troca as cidades de lugar. A cidade de partida (primeira posição) é preservada.
    
    Parâmetros
    ----------
    individuo : Individuo
        O indivíduo a ser mutado
    probabilidade_mutacao : float
        Probabilidade de ocorrência da mutação (0.0 a 1.0)
        Exemplo: 0.01 = 1% de chance
    
    Retorna
    -------
    Individuo
        Novo indivíduo com a mutação aplicada (ou cópia sem mutação)
    
    Notas
    -----
    - A cidade de partida (primeira e última posição) nunca é movida
    - A mutação garante que nenhuma cidade interna é perdida ou duplicada
    - Se a probabilidade não for atingida, retorna uma cópia idêntica

    Exemplo
    -------
    >>> # cromossomo original: [SP, Campinas, Santos, Sorocaba, SP]
    >>> # Após mutação (swap): [SP, Santos, Campinas, Sorocaba, SP]
    """
    individuo_mutado = copy.deepcopy(individuo)
    
    # Verificar se deve ocorrer mutação
    if random.random() >= probabilidade_mutacao:
        return individuo_mutado
    
    # Garantir que há pelo menos 2 cidades internas para fazer swap
    # (cromossomo: [partida, ..., partida] — mínimo: [p, A, B, p] = len 4)
    if len(individuo_mutado.cromossomo) < 4:
        return individuo_mutado

    # Selecionar duas posições adjacentes (excluindo a primeira e a última — ambas são partida)
    # Índices válidos para indice1: 1 até len-3, pois indice2 = indice1+1 nunca pode ser len-1
    indice1 = random.randint(1, len(individuo_mutado.cromossomo) - 3)
    indice2 = indice1 + 1
    
    # Fazer o swap
    individuo_mutado.cromossomo[indice1], individuo_mutado.cromossomo[indice2] = \
        individuo_mutado.cromossomo[indice2], individuo_mutado.cromossomo[indice1]
    
    return individuo_mutado


# =============================================================================
# Operador de seleção alternativo: Torneio
# =============================================================================

def selecionar_por_torneio(
    populacao: list[Individuo],
    quantidade: int,
    tamanho_torneio: int = 3,
) -> list[Individuo]:
    """
    Seleciona indivíduos via torneio probabilístico.

    Em cada rodada sorteia `tamanho_torneio` candidatos aleatórios da população
    e escolhe o de menor aptidão. Menos suscetível à convergência prematura que
    o truncamento puro, pois indivíduos medianos ainda têm chance de ser
    selecionados.

    Parâmetros
    ----------
    populacao : list[Individuo]
    quantidade : int — número de indivíduos a selecionar.
    tamanho_torneio : int — candidatos por rodada de torneio (padrão=3).

    Retorna
    -------
    list[Individuo]

    Notas
    -----
    Por ser estocástico, o retorno NÃO garante incluir o melhor indivíduo da
    população — em populações grandes é comum que ele nunca seja sorteado em
    nenhuma rodada. Por isso, ao combinar este operador com elitismo, a elite a
    preservar deve ser recalculada separadamente via `seleciona_melhores_individuos`
    (é exatamente o que `RotaService.calcular_rota` faz), em vez de reaproveitar o
    resultado desta função como se fosse a elite real.
    """
    selecionados: list[Individuo] = []
    k = min(tamanho_torneio, len(populacao))
    for _ in range(quantidade):
        candidatos = random.choices(populacao, k=k)
        vencedor = min(candidatos, key=lambda ind: ind.calcular_aptidao())
        selecionados.append(vencedor)
    return selecionados


# =============================================================================
# Operador de crossover alternativo: ERX
# =============================================================================

def cruzamento_erx(parent1: Individuo, parent2: Individuo, partida: Cidade) -> Individuo:
    """
    Realiza cruzamento ERX (Edge Recombination Crossover).

    Constrói uma tabela de adjacências combinando as arestas de ambos os pais
    e gera um filho que maximiza o reaproveitamento de conexões existentes.
    É o operador de crossover mais eficaz para TSP puro porque preserva arestas
    de qualidade em vez de apenas a ordem relativa das cidades.

    Algoritmo
    ---------
    1. Para cada cidade, listar seus vizinhos nos dois cromossomos (sem duplicatas).
    2. Iniciar o filho com a primeira cidade interna de parent1.
    3. A cada passo escolher como próxima o vizinho disponível com MENOS
       adjacências restantes (mais restrito). Empate resolvido por sorteio.
    4. Se não houver vizinhos disponíveis, escolher aleatoriamente entre as
       cidades ainda não visitadas.

    Parâmetros
    ----------
    parent1 : Individuo
    parent2 : Individuo
    partida : Cidade

    Retorna
    -------
    Individuo
    """
    cidades_internas = parent1.cromossomo[1:-1]

    if not cidades_internas:
        return parent1.copiar()

    mapa_cidades: dict[int, Cidade] = {}
    for c in parent1.cromossomo:
        mapa_cidades[c.cod_ibge] = c
    for c in parent2.cromossomo:
        mapa_cidades[c.cod_ibge] = c

    # Tabela de adjacências: cod_ibge → conjunto de vizinhos
    adjacencias: dict[int, set[int]] = {c.cod_ibge: set() for c in cidades_internas}

    for cromossomo in [parent1.cromossomo, parent2.cromossomo]:
        internas = cromossomo[1:-1]
        n = len(internas)
        for i, cidade in enumerate(internas):
            if cidade.cod_ibge not in adjacencias:
                continue
            if i > 0:
                adjacencias[cidade.cod_ibge].add(internas[i - 1].cod_ibge)
            if i < n - 1:
                adjacencias[cidade.cod_ibge].add(internas[i + 1].cod_ibge)

    nao_visitados: set[int] = {c.cod_ibge for c in cidades_internas}
    filho_cromossomo: list[Cidade] = [partida]

    # Inicia pelo primeiro gene de parent1
    atual_cod = parent1.cromossomo[1].cod_ibge

    while nao_visitados:
        if atual_cod not in nao_visitados:
            atual_cod = random.choice(list(nao_visitados))

        nao_visitados.discard(atual_cod)
        filho_cromossomo.append(mapa_cidades[atual_cod])

        # Remove a cidade visitada de todas as listas de adjacência
        for adj in adjacencias.values():
            adj.discard(atual_cod)

        if not nao_visitados:
            break

        # Escolhe o próximo: vizinho disponível mais restrito
        vizinhos = [c for c in adjacencias.get(atual_cod, set()) if c in nao_visitados]
        if vizinhos:
            atual_cod = min(vizinhos, key=lambda c: len(adjacencias.get(c, set())))
        else:
            atual_cod = random.choice(list(nao_visitados))

    filho_cromossomo.append(partida)
    return Individuo(partida, filho_cromossomo, parent1.capacidade_veiculo_kg)


# =============================================================================
# Operador de mutação alternativo: Or-opt
# =============================================================================

def mutacao_or_opt(individuo: Individuo, probabilidade_mutacao: float) -> Individuo:
    """
    Realiza mutação Or-opt: remove um segmento de 1 a 3 cidades e o reinsere
    em uma posição aleatória diferente do cromossomo.

    Mais agressiva que o swap adjacente pois pode realocar cidades a longas
    distâncias na rota, escapando de ótimos locais que o swap não alcança.
    A cidade de partida (posições 0 e -1) nunca é movida.

    Parâmetros
    ----------
    individuo : Individuo
    probabilidade_mutacao : float

    Retorna
    -------
    Individuo — com Or-opt aplicado (ou cópia sem mutação).
    """
    if random.random() >= probabilidade_mutacao:
        return individuo.copiar()

    cromossomo = list(individuo.cromossomo)
    n = len(cromossomo)

    # Mínimo: [partida, A, B, C, partida] para mover 1 cidade e ainda ter reinserção
    if n < 5:
        return individuo.copiar()

    max_seg = min(3, n - 3)
    tamanho_seg = random.randint(1, max_seg)
    pos_inicio = random.randint(1, n - 2 - tamanho_seg)
    segmento = cromossomo[pos_inicio: pos_inicio + tamanho_seg]

    # Remove o segmento
    resto = cromossomo[:pos_inicio] + cromossomo[pos_inicio + tamanho_seg:]

    # Posições válidas para reinserção (excluindo a posição original e as extremidades)
    posicoes_validas = [p for p in range(1, len(resto) - 1) if p != pos_inicio]
    if not posicoes_validas:
        return individuo.copiar()

    pos_insercao = random.choice(posicoes_validas)
    novo_cromossomo = resto[:pos_insercao] + segmento + resto[pos_insercao:]
    return Individuo(individuo.partida, novo_cromossomo, individuo.capacidade_veiculo_kg)


# =============================================================================
# Busca local: 2-opt
# =============================================================================

def busca_local_2opt(individuo: Individuo, max_passagens: int = 1) -> Individuo:
    """
    Aplica busca local 2-opt ao cromossomo.

    A cada passagem testa todos os pares de arestas (i, j) e inverte o segmento
    entre eles se isso reduzir a distância total. Repete até não encontrar melhora
    ou atingir `max_passagens`.

    Notas
    -----
    Complexidade O(n²) por passagem. Para rotas grandes ou populações numerosas,
    ativar o 2-opt aumenta significativamente o tempo de execução — recomenda-se
    reduzir `tamanho_populacao` e `epocas` ao usá-lo. Para instâncias pequenas
    (poucas dezenas de cidades) o 2-opt costuma encontrar uma rota já ótima (ou
    muito próxima) em poucas gerações; épocas configuradas além desse ponto de
    convergência não trazem ganho adicional, apenas custo de processamento.

    Parâmetros
    ----------
    individuo : Individuo
    max_passagens : int — limite de passagens (padrão=1 para controlar custo).

    Retorna
    -------
    Individuo — com rota localmente otimizada.
    """
    cromossomo = list(individuo.cromossomo)
    n = len(cromossomo)

    if n < 5:
        return individuo.copiar()

    for _ in range(max_passagens):
        melhorou = False
        for i in range(1, n - 2):
            for j in range(i + 1, n - 1):
                d_atual = (
                    cromossomo[i - 1].distancia_para(cromossomo[i])
                    + cromossomo[j].distancia_para(cromossomo[j + 1])
                )
                d_nova = (
                    cromossomo[i - 1].distancia_para(cromossomo[j])
                    + cromossomo[i].distancia_para(cromossomo[j + 1])
                )
                if d_nova < d_atual - 1e-9:
                    cromossomo[i: j + 1] = list(reversed(cromossomo[i: j + 1]))
                    melhorou = True
        if not melhorou:
            break

    return Individuo(individuo.partida, cromossomo, individuo.capacidade_veiculo_kg)


# =============================================================================
# Inicialização alternativa: vizinho mais próximo
# =============================================================================

def gerar_individuo_vizinho_mais_proximo(
    partida: Cidade,
    cidades: list[Cidade],
    capacidade_veiculo_kg: float | None = None,
) -> Individuo:
    """
    Gera um indivíduo usando a heurística gulosa do vizinho mais próximo.

    A partir da cidade de partida, visita sempre a cidade não visitada mais
    próxima até completar a rota. Produz uma solução inicial de qualidade
    superior à aleatória, acelerando a convergência do AG.

    Parâmetros
    ----------
    partida : Cidade
    cidades : list[Cidade]

    Retorna
    -------
    Individuo — rota construída por heurística gulosa.
    """
    nao_visitadas = [c for c in cidades if c.cod_ibge != partida.cod_ibge]
    rota: list[Cidade] = [partida]
    atual = partida
    while nao_visitadas:
        mais_proximo = min(nao_visitadas, key=lambda c: atual.distancia_para(c))
        rota.append(mais_proximo)
        nao_visitadas.remove(mais_proximo)
        atual = mais_proximo
    rota.append(partida)
    return Individuo(partida, rota, capacidade_veiculo_kg)


# =============================================================================
# Operador de mutação alternativo: Inversão
# =============================================================================

def mutacao_inversao(individuo: Individuo, probabilidade_mutacao: float) -> Individuo:
    """
    Realiza mutação por inversão de um segmento do cromossomo.
    
    Com uma dada probabilidade, seleciona um segmento aleatório do cromossomo
    (entre dois índices) e inverte a ordem das cidades nesse segmento.
    A cidade de partida (primeira posição) é preservada.
    
    Parâmetros
    ----------
    individuo : Individuo
        O indivíduo a ser mutado
    probabilidade_mutacao : float
        Probabilidade de ocorrência da mutação (0.0 a 1.0)
        Exemplo: 0.05 = 5% de chance
    
    Retorna
    -------
    Individuo
        Novo indivíduo com a mutação por inversão aplicada (ou cópia sem mutação)
    
    Notas
    -----
    - A cidade de partida (primeira e última posição) é sempre preservada
    - Um segmento de 2 a N cidades internas pode ser invertido
    - A mutação por inversão explora o espaço de soluções de forma mais agressiva
      que a mutação simples, útil para escapar de mínimos locais

    Exemplo
    -------
    >>> # cromossomo original: [SP, Campinas, Santos, Sorocaba, Ribeirão Preto, SP]
    >>> # Após inversão do segmento [Santos, Sorocaba]:
    >>> # resultado: [SP, Campinas, Sorocaba, Santos, Ribeirão Preto, SP]
    """
    individuo_mutado = copy.deepcopy(individuo)
    
    # Verificar se deve ocorrer mutação
    if random.random() >= probabilidade_mutacao:
        return individuo_mutado
    
    # Garantir que há pelo menos 3 cidades internas para inverter um segmento
    # (cromossomo: [partida, ..., partida] — mínimo: [p, A, B, C, p] = len 5)
    if len(individuo_mutado.cromossomo) < 5:
        return individuo_mutado

    # Selecionar dois índices para delimitar o segmento
    # (excluindo a primeira e a última posição — ambas são partida)
    indice1 = random.randint(1, len(individuo_mutado.cromossomo) - 4)
    indice2 = random.randint(indice1 + 2, len(individuo_mutado.cromossomo) - 2)
    
    # Inverter o segmento entre indice1 e indice2 (inclusivo)
    individuo_mutado.cromossomo[indice1:indice2 + 1] = \
        reversed(individuo_mutado.cromossomo[indice1:indice2 + 1])

    return individuo_mutado


# =============================================================================
# Métricas de diagnóstico da população
# =============================================================================

def calcular_estatisticas_populacao(populacao: list[Individuo]) -> dict[str, float]:
    """
    Calcula métricas agregadas da população para diagnóstico da execução do AG.

    Complementa `seleciona_melhores_individuos` (que só olha o melhor indivíduo):
    aqui o objetivo é caracterizar a população inteira num dado momento, para
    permitir diagnosticar convergência prematura (perda de diversidade antes da
    aptidão estabilizar) e o comportamento coletivo da busca, não só do vencedor.

    Parâmetros
    ----------
    populacao : list[Individuo]

    Retorna
    -------
    dict com:
    - "aptidao_media": média de `aptidao` (mesma convenção de minimização) entre
      todos os indivíduos da população.
    - "aptidao_pior": MAIOR valor de `aptidao` da população (pior sob a convenção
      de minimização — não confundir com "menor").
    - "diversidade": proporção de arestas distintas (segmentos entre cidades
      consecutivas na rota, sem direção) em uso pela população em relação ao
      máximo teoricamente possível dado o tamanho da população e do problema.
      Varia de 0.0 (população inteira compartilha a mesma rota) a 1.0 (arestas
      tão variadas quanto o espaço de busca permite). Calculada em uma única
      passagem O(pop×n) — não faz comparação par a par entre indivíduos
      (O(pop²)), que seria custosa demais para populações grandes.

    Notas
    -----
    Chama `calcular_aptidao()` em cada indivíduo (efeito colateral inofensivo:
    recalcula os mesmos valores caso já tenham sido computados nesta geração).
    """
    aptidoes = [ind.calcular_aptidao() for ind in populacao]
    aptidao_media = sum(aptidoes) / len(aptidoes)
    aptidao_pior = max(aptidoes)

    arestas_vistas: set[frozenset] = set()
    n_cidades = 0
    for ind in populacao:
        cromossomo = ind.cromossomo
        n_cidades = len(cromossomo) - 1
        for i in range(n_cidades):
            arestas_vistas.add(frozenset((cromossomo[i].cod_ibge, cromossomo[i + 1].cod_ibge)))

    if n_cidades > 1:
        maximo_possivel = min(len(populacao) * n_cidades, n_cidades * (n_cidades - 1) // 2)
    else:
        maximo_possivel = 0

    diversidade = len(arestas_vistas) / maximo_possivel if maximo_possivel else 0.0

    return {
        "aptidao_media": aptidao_media,
        "aptidao_pior": aptidao_pior,
        "diversidade": diversidade,
    }
