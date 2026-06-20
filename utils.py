
# =============================================================================
# Função utilitária: gera a matriz de distâncias a partir de uma lista de cidades
# =============================================================================
 
import copy
import random
from typing import Optional

from Individuo import Individuo
from cidade import Cidade


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
                      cada um começando obrigatoriamente com a cidade de partida.
    
    Notas
    -----
    - Cada indivíduo começará obrigatoriamente com a cidade de partida.
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
    
    populacao = []
    cromossomos_vistos = set()  # Rastreia cromossomos únicos pelos IDs
    
    # Processar melhores indivíduos (se fornecidos)
    if melhores_individuos:
        if not isinstance(melhores_individuos, list):
            raise ValueError("melhores_individuos deve ser uma lista de Indivíduos.")
        
        if len(melhores_individuos) >= quantidade:
            raise ValueError(
                f"A quantidade de melhores indivíduos ({len(melhores_individuos)}) "
                f"não pode ser maior ou igual à quantidade total ({quantidade})."
            )
        
        # Validar e incluir melhores indivíduos
        for i, individuo in enumerate(melhores_individuos):
            # Verifica se começa com a partida
            if individuo.cromossomo[0].id != partida.id:
                raise ValueError(
                    f"O indivíduo {i+1} dos melhores não começa com a cidade de partida ({partida.nome}). "
                    f"Começa com: {individuo.cromossomo[0].nome}."
                )
            
            # Registra o cromossomo como visto
            cromossomo_tupla = tuple(c.id for c in individuo.cromossomo)
            cromossomos_vistos.add(cromossomo_tupla)
            populacao.append(individuo)
    
    # Calcula quantos novos indivíduos precisam ser gerados
    quantidade_novos = quantidade - len(populacao)
    tentativas = 0
    max_tentativas = quantidade_novos * 100  # Evita loop infinito
    
    # Loop de geração com validação de unicidade
    while len(populacao) < quantidade and tentativas < max_tentativas:
        # Cria um novo indivíduo (começa com partida automaticamente)
        individuo = Individuo(partida, cidades)
        
        # Cria uma tupla de IDs para comparação eficiente
        cromossomo_tupla = tuple(c.id for c in individuo.cromossomo)
        
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
    - O cromossomo filho sempre começa com a cidade de partida
    - O cruzamento preserva a ordem relativa das cidades
    - Nenhuma cidade é duplicada no cromossomo filho
    
    Exemplo
    -------
    >>> # parent1.cromossomo = [SP, Campinas, Santos, Sorocaba, ...]
    >>> # parent2.cromossomo = [SP, Sorocaba, Santos, Campinas, ...]
    >>> # filho pode ser: [SP, Campinas, Sorocaba, Santos, ...]
    """
    cromossomo_p1 = parent1.cromossomo
    cromossomo_p2 = parent2.cromossomo
    
    length = len(cromossomo_p1)
    
    # Escolher dois índices aleatórios para o segmento de cruzamento
    # (excluindo a primeira posição que é a cidade de partida)
    if length < 3:
        # Se houver menos de 3 cidades, apenas retornar uma cópia do parent1
        filho = Individuo(partida, [c for c in cromossomo_p1])
        return filho
    
    start_index = random.randint(1, length - 2)
    end_index = random.randint(start_index + 1, length)
    
    # Copiar o segmento de parent1
    segmento = cromossomo_p1[start_index:end_index]
    
    # Identificar as cidades que não estão no segmento
    cidades_no_segmento = {cidade.id for cidade in segmento}
    
    # Preencher as posições restantes com cidades de parent2 em ordem
    cidades_restantes = [cidade for cidade in cromossomo_p2 
                        if cidade.id not in cidades_no_segmento and cidade.id != partida.id]
    
    # Construir o cromossomo do filho
    filho_cromossomo = [partida]  # Começa com a partida
    
    # Adicionar cidades antes do segmento (de parent2)
    quantidade_antes = start_index - 1
    filho_cromossomo.extend(cidades_restantes[:quantidade_antes])
    
    # Adicionar o segmento
    filho_cromossomo.extend(segmento)
    
    # Adicionar cidades após o segmento (de parent2)
    filho_cromossomo.extend(cidades_restantes[quantidade_antes:])
    
    # Criar indivíduo filho com o novo cromossomo
    filho = Individuo(partida, [partida] + [c for c in cromossomo_p1 if c.id != partida.id])
    filho.cromossomo = filho_cromossomo
    
    return filho


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
    - A cidade de partida (primeira posição) nunca é movida
    - A mutação garante que nenhuma cidade é perdida ou duplicada
    - Se a probabilidade não for atingida, retorna uma cópia idêntica
    
    Exemplo
    -------
    >>> # cromossomo original: [SP, Campinas, Santos, Sorocaba]
    >>> # Após mutação (swap): [SP, Santos, Campinas, Sorocaba]
    """
    individuo_mutado = copy.deepcopy(individuo)
    
    # Verificar se deve ocorrer mutação
    if random.random() >= probabilidade_mutacao:
        return individuo_mutado
    
    # Garantir que há pelo menos 2 cidades para fazer swap
    if len(individuo_mutado.cromossomo) < 3:
        return individuo_mutado
    
    # Selecionar duas posições adjacentes aleatoriamente (excluindo a primeira)
    # Índices válidos: 1 até len-2 (para permitir swap com o próximo)
    indice1 = random.randint(1, len(individuo_mutado.cromossomo) - 2)
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
    - A cidade de partida (primeira posição) é sempre preservada
    - Um segmento de 2 a N cidades pode ser invertido
    - A mutação por inversão explora o espaço de soluções de forma mais agressiva
      que a mutação simples, útil para escapar de mínimos locais
    
    Exemplo
    -------
    >>> # cromossomo original: [SP, Campinas, Santos, Sorocaba, Ribeirão Preto]
    >>> # Após inversão do segmento [Santos, Sorocaba]:
    >>> # resultado: [SP, Campinas, Sorocaba, Santos, Ribeirão Preto]
    """
    individuo_mutado = copy.deepcopy(individuo)
    
    # Verificar se deve ocorrer mutação
    if random.random() >= probabilidade_mutacao:
        return individuo_mutado
    
    # Garantir que há pelo menos 3 cidades para inverter um segmento
    if len(individuo_mutado.cromossomo) < 4:
        return individuo_mutado
    
    # Selecionar dois índices aleatórios para delimitar o segmento
    # (excluindo a primeira posição que é a cidade de partida)
    indice1 = random.randint(1, len(individuo_mutado.cromossomo) - 3)
    indice2 = random.randint(indice1 + 2, len(individuo_mutado.cromossomo) - 1)
    
    # Inverter o segmento entre indice1 e indice2 (inclusivo)
    individuo_mutado.cromossomo[indice1:indice2 + 1] = \
        reversed(individuo_mutado.cromossomo[indice1:indice2 + 1])
    
    return individuo_mutado
 
 