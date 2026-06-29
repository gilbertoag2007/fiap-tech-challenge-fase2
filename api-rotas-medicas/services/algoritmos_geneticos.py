
# =============================================================================
# Função utilitária: gera a matriz de distâncias a partir de uma lista de cidades
# =============================================================================
 
import copy
import random
from math import factorial
from typing import Optional

from models.Individuo import Individuo
from models.cidade import Cidade


def gerar_matriz_distancias(cidades: list[Cidade]) -> list[list[float]]:
    """
    Gera uma matriz NxN com as distâncias geodésicas (em KM) entre todas as cidades.

    Parâmetros
    ----------
    cidades : list[Cidade]

    Retorna
    -------
    list[list[float]] — matriz simétrica onde matriz[i][j] = distância entre
                        cidades[i] e cidades[j]
    """
    n = len(cidades)
    matriz = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            dist = cidades[i].distancia_para(cidades[j])
            matriz[i][j] = dist
            matriz[j][i] = dist  # matriz simétrica
    header = f"{'':22}" + "".join(f"{c.nome[:10]:>12}" for c in cidades)
    print(header)
    for i, c in enumerate(cidades):
        linha = f"  {c.nome:<20}" + "".join(f"{matriz[i][j]:>12.1f}" for j in range(len(cidades)))
        print(linha)
            
    return matriz

def gerar_individuo_aleatorio(partida: Cidade, cidades: list[Cidade]) -> Individuo:
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
    return Individuo(partida, [partida] + outras + [partida])


def seleciona_melhores_individuos(populacao: list[Individuo], quantidade: int) -> list[Individuo]:
    """Seleciona os n indivíduos com as menores distâncias (melhores aptidões) da população."""
    return sorted(populacao, key=lambda x: x.calcular_aptidao())[:quantidade]      


def gerar_populacao_aleatoria(
    quantidade: int, 
    partida: Cidade, 
    cidades: list[Cidade],
    melhores_individuos: Optional[list[Individuo]] = None
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
        individuo = gerar_individuo_aleatorio(partida, cidades)
        
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
# Operadores genéticos: Crossover
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
        return Individuo(partida, list(cromossomo_p1))

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

    return Individuo(partida, filho_cromossomo)


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
 
 