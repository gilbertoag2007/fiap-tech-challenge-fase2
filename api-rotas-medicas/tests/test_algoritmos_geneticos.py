"""
Testes de algoritmos_geneticos.py

Estratégia
----------
1. Testes unitários: cada função é validada isoladamente quanto aos invariantes
   do domínio (rota circular, sem duplicatas, sem perda/ganho de cidades).
2. Teste de integração combinatória: reproduz o laço evolutivo de
   RotaService.calcular_rota (sem chamar o LLM) e o executa para todas as
   combinações de tipo_selecao x tipo_inicializacao x tipo_mutacao x elitismo
   expostas ao usuário no frontend (2x2x4x2 = 32 combinações), com população e
   número de épocas pequenos para manter o custo baixo.
3. tipo_crossover ('ox'/'erx') e usar_2opt são testados à parte (não entram na
   combinatória de 32) para não explodir o número de execuções.
"""
import random
import sys
from math import factorial
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models.cidade import Cidade
from models.Individuo import Individuo
from models.produto import Produto
from services import algoritmos_geneticos as ag
from services.rota_service import RotaService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _cidades(n: int = 8) -> list[Cidade]:
    """N cidades com produtos de prioridade alternada (a partida não tem produto)."""
    cidades = [Cidade(0, "Partida", "SP", 0.0, 0.0, "Sudeste", None)]
    for i in range(1, n):
        prioridade = 1 if i % 2 == 0 else 2
        produto = Produto(i, f"Produto{i}", prioridade)
        cidades.append(Cidade(i, f"Cidade{i}", "SP", i * 0.5, i * 0.3, "Sudeste", produto))
    return cidades


def _assert_individuo_valido(ind: Individuo, cidades: list[Cidade], partida: Cidade) -> None:
    assert ind.is_valido()
    assert ind.cromossomo[0].cod_ibge == partida.cod_ibge
    assert ind.cromossomo[-1].cod_ibge == partida.cod_ibge
    ids_esperados = {c.cod_ibge for c in cidades}
    ids_obtidos = {c.cod_ibge for c in ind.cromossomo[:-1]}
    assert ids_esperados == ids_obtidos
    assert len(ind.cromossomo) == len(cidades) + 1


# ---------------------------------------------------------------------------
# Inicialização de população
# ---------------------------------------------------------------------------

def test_gerar_individuo_aleatorio_e_valido():
    cidades = _cidades(8)
    partida = cidades[0]
    ind = ag.gerar_individuo_aleatorio(partida, cidades)
    _assert_individuo_valido(ind, cidades, partida)


def test_gerar_individuo_vizinho_mais_proximo_e_guloso_e_valido():
    cidades = _cidades(8)
    partida = cidades[0]
    ind = ag.gerar_individuo_vizinho_mais_proximo(partida, cidades)
    _assert_individuo_valido(ind, cidades, partida)
    # heurística gulosa: cada passo deve ser o vizinho não visitado mais próximo
    visitados = {partida.cod_ibge}
    for i in range(len(ind.cromossomo) - 2):
        atual = ind.cromossomo[i]
        prox = ind.cromossomo[i + 1]
        candidatos = [c for c in cidades if c.cod_ibge not in visitados]
        esperado = min(candidatos, key=lambda c: atual.distancia_para(c))
        assert prox.cod_ibge == esperado.cod_ibge
        visitados.add(prox.cod_ibge)


def test_gerar_populacao_aleatoria_tamanho_e_unicidade():
    cidades = _cidades(8)
    partida = cidades[0]
    pop = ag.gerar_populacao_aleatoria(15, partida, cidades)
    assert len(pop) == 15
    tuplas = {tuple(c.cod_ibge for c in ind.cromossomo) for ind in pop}
    assert len(tuplas) == 15
    for ind in pop:
        _assert_individuo_valido(ind, cidades, partida)


def test_gerar_populacao_aleatoria_ajusta_quantidade_acima_do_limite_combinatorio():
    cidades = _cidades(4)  # (4-1)! = 6 rotas únicas possíveis
    partida = cidades[0]
    pop = ag.gerar_populacao_aleatoria(1000, partida, cidades)
    assert len(pop) == factorial(len(cidades) - 1)


def test_gerar_populacao_aleatoria_inclui_melhores_individuos():
    cidades = _cidades(8)
    partida = cidades[0]
    melhor = ag.gerar_individuo_vizinho_mais_proximo(partida, cidades)
    pop = ag.gerar_populacao_aleatoria(10, partida, cidades, melhores_individuos=[melhor])
    assert len(pop) == 10
    tuplas = {tuple(c.cod_ibge for c in ind.cromossomo) for ind in pop}
    assert tuple(c.cod_ibge for c in melhor.cromossomo) in tuplas


@pytest.mark.parametrize("cidades_vazias_ou_sem_partida", ["vazia", "sem_partida"])
def test_gerar_populacao_aleatoria_validacoes(cidades_vazias_ou_sem_partida):
    if cidades_vazias_ou_sem_partida == "vazia":
        with pytest.raises(ValueError):
            ag.gerar_populacao_aleatoria(5, Cidade(0, "X", "SP", 0, 0, None), [])
    else:
        cidades = _cidades(5)
        outra = Cidade(999, "Fora", "SP", 1, 1, None)
        with pytest.raises(ValueError):
            ag.gerar_populacao_aleatoria(5, outra, cidades)


def test_gerar_populacao_aleatoria_rejeita_melhor_individuo_invalido():
    cidades = _cidades(5)
    partida = cidades[0]
    individuo_invalido = Individuo(partida, [cidades[1], cidades[2], cidades[1]])
    with pytest.raises(ValueError):
        ag.gerar_populacao_aleatoria(5, partida, cidades, melhores_individuos=[individuo_invalido])


# ---------------------------------------------------------------------------
# Seleção
# ---------------------------------------------------------------------------

def test_seleciona_melhores_individuos_ordena_por_aptidao_ascendente():
    cidades = _cidades(8)
    partida = cidades[0]
    pop = ag.gerar_populacao_aleatoria(10, partida, cidades)
    melhores = ag.seleciona_melhores_individuos(pop, 4)
    assert len(melhores) == 4
    aptidoes = [ind.calcular_aptidao() for ind in melhores]
    assert aptidoes == sorted(aptidoes)
    assert min(ind.calcular_aptidao() for ind in pop) == aptidoes[0]


def test_selecionar_por_torneio_retorna_membros_da_populacao():
    cidades = _cidades(8)
    partida = cidades[0]
    pop = ag.gerar_populacao_aleatoria(10, partida, cidades)
    ids_pop = {id(ind) for ind in pop}
    selecionados = ag.selecionar_por_torneio(pop, 6, tamanho_torneio=3)
    assert len(selecionados) == 6
    assert all(id(ind) in ids_pop for ind in selecionados)


def test_selecionar_por_torneio_tende_a_favorecer_o_melhor(monkeypatch):
    cidades = _cidades(8)
    partida = cidades[0]
    pop = ag.gerar_populacao_aleatoria(10, partida, cidades)
    melhor = ag.seleciona_melhores_individuos(pop, 1)[0]
    random.seed(42)
    selecionados = ag.selecionar_por_torneio(pop, 50, tamanho_torneio=5)
    freq_melhor = sum(1 for s in selecionados if s is melhor)
    freq_media_esperada = 50 / len(pop)
    assert freq_melhor >= freq_media_esperada  # melhor é escolhido com frequência >= média


# ---------------------------------------------------------------------------
# Crossover
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("operador", ["ox", "erx"])
def test_crossover_gera_filho_valido(operador):
    cidades = _cidades(8)
    partida = cidades[0]
    p1 = ag.gerar_individuo_aleatorio(partida, cidades)
    p2 = ag.gerar_individuo_aleatorio(partida, cidades)
    funcao = ag.cruzamento_ox if operador == "ox" else ag.cruzamento_erx
    filho = funcao(p1, p2, partida)
    _assert_individuo_valido(filho, cidades, partida)


def test_cruzamento_ox_cromossomo_curto_retorna_copia_do_pai1():
    cidades = _cidades(3)  # cromossomo len 4: [partida, A, B, partida]
    partida = cidades[0]
    p1 = ag.gerar_individuo_aleatorio(partida, cidades)
    p2 = ag.gerar_individuo_aleatorio(partida, cidades)
    filho = ag.cruzamento_ox(p1, p2, partida)
    assert [c.cod_ibge for c in filho.cromossomo] == [c.cod_ibge for c in p1.cromossomo]


# ---------------------------------------------------------------------------
# Mutação
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("operador", ["swap", "inversao", "or_opt"])
def test_mutacao_com_probabilidade_zero_nao_altera_cromossomo(operador):
    cidades = _cidades(8)
    partida = cidades[0]
    ind = ag.gerar_individuo_aleatorio(partida, cidades)
    funcao = {"swap": ag.mutacao_simples, "inversao": ag.mutacao_inversao, "or_opt": ag.mutacao_or_opt}[operador]
    mutado = funcao(ind, 0.0)
    assert [c.cod_ibge for c in mutado.cromossomo] == [c.cod_ibge for c in ind.cromossomo]


@pytest.mark.parametrize("operador", ["swap", "inversao", "or_opt"])
def test_mutacao_com_probabilidade_um_preserva_validade(operador):
    cidades = _cidades(8)
    partida = cidades[0]
    ind = ag.gerar_individuo_aleatorio(partida, cidades)
    funcao = {"swap": ag.mutacao_simples, "inversao": ag.mutacao_inversao, "or_opt": ag.mutacao_or_opt}[operador]
    mutado = funcao(ind, 1.0)
    _assert_individuo_valido(mutado, cidades, partida)


@pytest.mark.parametrize("operador,n_cidades", [("swap", 3), ("inversao", 4), ("or_opt", 4)])
def test_mutacao_cromossomo_pequeno_nao_quebra(operador, n_cidades):
    """Cromossomos abaixo do tamanho mínimo devem retornar cópia válida, sem exceção."""
    cidades = _cidades(n_cidades)
    partida = cidades[0]
    ind = ag.gerar_individuo_aleatorio(partida, cidades)
    funcao = {"swap": ag.mutacao_simples, "inversao": ag.mutacao_inversao, "or_opt": ag.mutacao_or_opt}[operador]
    mutado = funcao(ind, 1.0)
    _assert_individuo_valido(mutado, cidades, partida)


# ---------------------------------------------------------------------------
# Busca local 2-opt
# ---------------------------------------------------------------------------

def test_busca_local_2opt_nunca_piora_e_mantem_validade():
    cidades = _cidades(8)
    partida = cidades[0]
    ind = ag.gerar_individuo_aleatorio(partida, cidades)
    dist_antes = ind.calcular_aptidao() and ind.distancia
    otimizado = ag.busca_local_2opt(ind, max_passagens=2)
    _assert_individuo_valido(otimizado, cidades, partida)
    otimizado.calcular_aptidao()
    assert otimizado.distancia <= dist_antes + 1e-6


# ---------------------------------------------------------------------------
# Métricas de diagnóstico da população
# ---------------------------------------------------------------------------

def test_calcular_estatisticas_populacao_media_e_pior_consistentes():
    cidades = _cidades(8)
    partida = cidades[0]
    pop = ag.gerar_populacao_aleatoria(10, partida, cidades)
    stats = ag.calcular_estatisticas_populacao(pop)

    aptidoes = [ind.calcular_aptidao() for ind in pop]
    assert stats["aptidao_pior"] == max(aptidoes)
    assert stats["aptidao_media"] == pytest.approx(sum(aptidoes) / len(aptidoes))
    # pior >= média >= melhor, sob a convenção de minimização
    assert stats["aptidao_pior"] >= stats["aptidao_media"] >= min(aptidoes)


def test_calcular_estatisticas_populacao_diversidade_minima_quando_identica():
    cidades = _cidades(8)
    partida = cidades[0]
    individuo = ag.gerar_individuo_aleatorio(partida, cidades)
    # população inteira com o mesmo cromossomo (mesmas arestas) — diversidade no piso
    # teórico: só as n arestas do próprio ciclo, sobre o máximo de arestas possível (C(n,2)).
    pop = [individuo.copiar() for _ in range(5)]
    stats = ag.calcular_estatisticas_populacao(pop)
    n = len(cidades)
    esperado = n / (n * (n - 1) / 2)
    assert stats["diversidade"] == pytest.approx(esperado)


def test_calcular_estatisticas_populacao_diversidade_entre_zero_e_um():
    cidades = _cidades(8)
    partida = cidades[0]
    pop = ag.gerar_populacao_aleatoria(20, partida, cidades)
    stats = ag.calcular_estatisticas_populacao(pop)
    assert 0.0 <= stats["diversidade"] <= 1.0


# ---------------------------------------------------------------------------
# Diagnóstico de priorização (RotaService._diagnostico_prioridade)
# ---------------------------------------------------------------------------

def test_diagnostico_prioridade_cidade_prioridade_1_logo_apos_partida():
    # partida (sem produto) + 1 cidade prioridade 1 na 1ª posição + 1 prioridade 2 na última
    partida = Cidade(0, "Partida", "SP", 0.0, 0.0, "Sudeste", None)
    c1 = Cidade(1, "Cidade1", "SP", 0.5, 0.3, "Sudeste", Produto(1, "Vacina", 1))
    c2 = Cidade(2, "Cidade2", "SP", 1.0, 0.6, "Sudeste", Produto(2, "Insumo", 2))
    individuo = Individuo(partida, [partida, c1, c2, partida])

    diagnostico = RotaService()._diagnostico_prioridade(individuo)
    assert diagnostico["cidades_prioridade_1"] == 1
    # c1 está na ordem_visita=2 (partida=1, c1=2, c2=3) de um total de 3 cidades
    assert diagnostico["posicao_media_prioridade_1_percentual"] == pytest.approx((2 / 3) * 100, abs=0.1)
    # c2 (prioridade 2) está na ordem_visita=3 — mais tarde na rota que a prioridade 1
    assert diagnostico["cidades_prioridade_2"] == 1
    assert diagnostico["posicao_media_prioridade_2_percentual"] == pytest.approx((3 / 3) * 100, abs=0.1)
    assert diagnostico["posicao_media_prioridade_2_percentual"] > diagnostico["posicao_media_prioridade_1_percentual"]


def test_diagnostico_prioridade_sem_cidades_prioridade_1_retorna_none():
    partida = Cidade(0, "Partida", "SP", 0.0, 0.0, "Sudeste", None)
    c1 = Cidade(1, "Cidade1", "SP", 0.5, 0.3, "Sudeste", Produto(1, "Insumo", 2))
    individuo = Individuo(partida, [partida, c1, partida])

    diagnostico = RotaService()._diagnostico_prioridade(individuo)
    assert diagnostico["cidades_prioridade_1"] == 0
    assert diagnostico["posicao_media_prioridade_1_percentual"] is None
    assert diagnostico["cidades_prioridade_2"] == 1
    assert diagnostico["posicao_media_prioridade_2_percentual"] is not None


# ---------------------------------------------------------------------------
# Intervalo de amostragem do historico_evolucao (RotaService._calcular_intervalo_amostra)
# ---------------------------------------------------------------------------

def test_intervalo_amostra_sem_parada_antecipada_usa_10_por_cento_das_epocas():
    intervalo = RotaService()._calcular_intervalo_amostra(
        epocas=1000, parada_antecipada_ativa=False, paciencia_parada_antecipada=30
    )
    assert intervalo == 100


def test_intervalo_amostra_com_parada_antecipada_usa_fracao_da_paciencia():
    # Caso real que motivou o ajuste: epocas=1000, paciência=30 — sem a correção,
    # o intervalo seria 100 e uma parada antecipada por volta da época 103
    # produziria só 1 ponto no histórico (insuficiente para desenhar uma linha).
    intervalo = RotaService()._calcular_intervalo_amostra(
        epocas=1000, parada_antecipada_ativa=True, paciencia_parada_antecipada=30
    )
    assert intervalo == 10
    # Uma parada na época 103 deve render ao menos 3 pontos amostrados antes dela.
    pontos_antes_da_parada = 103 // intervalo
    assert pontos_antes_da_parada >= 3


def test_intervalo_amostra_com_parada_antecipada_nunca_e_menor_que_1():
    intervalo = RotaService()._calcular_intervalo_amostra(
        epocas=50, parada_antecipada_ativa=True, paciencia_parada_antecipada=1
    )
    assert intervalo == 1


# ---------------------------------------------------------------------------
# Integração combinatória — reproduz o laço de RotaService sem o LLM,
# cobrindo as combinações de seleção x inicialização x mutação x elitismo
# que o usuário pode escolher no frontend.
# ---------------------------------------------------------------------------

def _executar_ag(tipo_selecao, tipo_inicializacao, tipo_mutacao, elitismo,
                  cidades, partida, epocas=4, tamanho_populacao=12, tamanho_elite=4,
                  probabilidade_mutacao=0.3, historico=None):
    """Reproduz o laço evolutivo de RotaService.calcular_rota (mesma lógica de produção).

    Se `historico` (lista) for informado, cada época adiciona a aptidão do melhor
    indivíduo daquela geração — usado para verificar monotonicidade do elitismo.
    """
    if tipo_inicializacao == "vizinho_mais_proximo":
        nn = ag.gerar_individuo_vizinho_mais_proximo(partida, cidades)
        populacao = ag.gerar_populacao_aleatoria(tamanho_populacao, partida, cidades, melhores_individuos=[nn])
    else:
        populacao = ag.gerar_populacao_aleatoria(tamanho_populacao, partida, cidades)

    for _ in range(epocas):
        if tipo_selecao == "torneio":
            melhores = ag.selecionar_por_torneio(populacao, tamanho_elite)
        else:
            melhores = ag.seleciona_melhores_individuos(populacao, tamanho_elite)

        # Elitismo: preserva sempre os verdadeiros melhores da população, independente
        # do método de seleção dos pais (torneio é estocástico e pode não sortear o
        # melhor indivíduo entre seus vencedores) — mesma lógica de rota_service.py.
        if elitismo == 1:
            elite = ag.seleciona_melhores_individuos(populacao, tamanho_elite) if tipo_selecao == "torneio" else melhores
            nova_populacao = list(elite)
        else:
            nova_populacao = []

        while len(nova_populacao) < tamanho_populacao:
            p1, p2 = random.choices(melhores, k=2)
            filho = ag.cruzamento_ox(p1, p2, partida)
            if tipo_mutacao == "swap":
                filho = ag.mutacao_simples(filho, probabilidade_mutacao)
            elif tipo_mutacao == "inversao":
                filho = ag.mutacao_inversao(filho, probabilidade_mutacao)
            elif tipo_mutacao == "or_opt":
                filho = ag.mutacao_or_opt(filho, probabilidade_mutacao)
            else:
                filho = ag.mutacao_simples(filho, probabilidade_mutacao)
                filho = ag.mutacao_inversao(filho, probabilidade_mutacao)
            nova_populacao.append(filho)
        populacao = nova_populacao

        if historico is not None:
            historico.append(ag.seleciona_melhores_individuos(populacao, 1)[0].calcular_aptidao())

    return ag.seleciona_melhores_individuos(populacao, 1)[0]


COMBINACOES = [
    (sel, init, mut, elit)
    for sel in ("truncamento", "torneio")
    for init in ("aleatoria", "vizinho_mais_proximo")
    for mut in ("swap", "inversao", "ambos", "or_opt")
    for elit in (0, 1)
]


@pytest.mark.parametrize("tipo_selecao,tipo_inicializacao,tipo_mutacao,elitismo", COMBINACOES)
def test_combinacoes_frontend_produzem_individuo_valido(tipo_selecao, tipo_inicializacao, tipo_mutacao, elitismo):
    random.seed(0)
    cidades = _cidades(7)
    partida = cidades[0]
    melhor = _executar_ag(tipo_selecao, tipo_inicializacao, tipo_mutacao, elitismo, cidades, partida)
    _assert_individuo_valido(melhor, cidades, partida)
    melhor.calcular_aptidao()
    assert melhor.distancia >= 0
    assert isinstance(melhor.aptidao, float)


@pytest.mark.parametrize("tipo_selecao", ["truncamento", "torneio"])
@pytest.mark.parametrize("seed", range(5))
def test_elitismo_nunca_piora_independente_do_tipo_selecao(tipo_selecao, seed):
    """Regressão: com elitismo=1, a aptidão do melhor indivíduo nunca deve piorar
    entre épocas, mesmo com tipo_selecao='torneio' (seleção estocástica dos pais).

    Bug original: o elitismo reaproveitava a mesma lista de vencedores do torneio
    como "elite", e o torneio pode não sortear o melhor indivíduo da população —
    fazendo-o se perder entre gerações. Corrigido em rota_service.py para sempre
    recalcular a elite real via seleciona_melhores_individuos quando elitismo=1.
    """
    random.seed(seed)
    cidades = _cidades(10)
    partida = cidades[0]
    historico: list[float] = []
    _executar_ag(
        tipo_selecao, "aleatoria", "ambos", elitismo=1,
        cidades=cidades, partida=partida,
        epocas=20, tamanho_populacao=30, tamanho_elite=8,
        historico=historico,
    )
    for anterior, atual in zip(historico, historico[1:]):
        assert atual <= anterior + 1e-9, f"aptidão piorou: {anterior} -> {atual}"


def test_elitismo_preserva_ou_melhora_melhor_individuo_entre_epocas():
    """Com elitismo=1, a aptidão do melhor indivíduo nunca deve piorar entre gerações."""
    random.seed(1)
    cidades = _cidades(7)
    partida = cidades[0]
    populacao = ag.gerar_populacao_aleatoria(12, partida, cidades)
    melhor_aptidao_anterior = ag.seleciona_melhores_individuos(populacao, 1)[0].calcular_aptidao()

    for _ in range(5):
        melhores = ag.seleciona_melhores_individuos(populacao, 4)
        nova_populacao = list(melhores)
        while len(nova_populacao) < 12:
            p1, p2 = random.choices(melhores, k=2)
            filho = ag.mutacao_inversao(ag.cruzamento_ox(p1, p2, partida), 0.3)
            nova_populacao.append(filho)
        populacao = nova_populacao
        melhor_atual = ag.seleciona_melhores_individuos(populacao, 1)[0].calcular_aptidao()
        assert melhor_atual <= melhor_aptidao_anterior + 1e-9
        melhor_aptidao_anterior = melhor_atual
