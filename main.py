from cidade import Cidade
from Individuo import Individuo
from algoritmos_geneticos import *
from produto import Produto
import matplotlib.pyplot as plt
import folium


# =============================================================================
# Geração da lista de produtos
# =============================================================================

def popular_produtos() -> list[Produto]:
    """Cria e retorna uma lista de produtos pré-definidos."""
    produtos_cadastrados = [
        Produto("Vacina A", prioridade=1),
        Produto("Vacina B", prioridade=1),
        Produto("Algodão", prioridade=2),
        Produto("Gase", prioridade=2),
        Produto("Anti-séptico", prioridade=2),
    ]
    
    print("=== Produtos cadastrados ===")
    for p in produtos_cadastrados:
        print(f"  {p.nome} - {p.prioridade}")

    return produtos_cadastrados


# =============================================================================
# Geração da lista de cidades
# =============================================================================
def popular_cidades() -> list[Cidade]:
    """Cria e retorna uma lista de cidades pré-definidas."""
    
    produtos_cadastrados = popular_produtos()
    
    cidades_cadastradas = [
        Cidade(0,  "São Paulo",           "SP", -23.5505, -46.6333),                       # partida
        Cidade(1,  "Campinas",            "SP", -22.9056, -47.0608, produto=produtos_cadastrados[0]),
        Cidade(2,  "Ribeirão Preto",      "SP", -21.1775, -47.8103, produto=produtos_cadastrados[1]),
        Cidade(3,  "Santos",              "SP", -23.9618, -46.3322, produto=produtos_cadastrados[0]),
        Cidade(4,  "Sorocaba",            "SP", -23.5015, -47.4526, produto=produtos_cadastrados[2]),
        Cidade(5,  "São José dos Campos", "SP", -23.1794, -45.8869, produto=produtos_cadastrados[0]),
        Cidade(6,  "Bauru",               "SP", -22.3246, -49.0961, produto=produtos_cadastrados[3]),
        Cidade(7,  "Presidente Prudente", "SP", -22.1256, -51.3889, produto=produtos_cadastrados[4]),
        Cidade(8,  "São Carlos",          "SP", -22.0154, -47.8910, produto=produtos_cadastrados[2]),
        Cidade(9,  "Piracicaba",          "SP", -22.7253, -47.6492, produto=produtos_cadastrados[3]),
    ]
    
    print("=== Cidades cadastradas ===")
    for c in cidades_cadastradas:
        print(f"  {c}")

    return cidades_cadastradas

# =============================================================================
# TESTE 1: Crossover (Order Crossover - OX)
# =============================================================================
 
def teste_crossover():
    """Testa o operador de cruzamento OX."""
    print("\n" + "="*80)
    print("TESTE 1: CRUZAMENTO (ORDER CROSSOVER - OX)")
    print("="*80)
    
    cidades = popular_cidades()
    partida = cidades[0]  # São Paulo
    
    # Criar dois indivíduos progenitores
    parent1 = gerar_individuo_aleatorio(partida, cidades)
    parent2 = gerar_individuo_aleatorio(partida, cidades)
    
    print("\n📍 Parent 1 (Progenitor 1):")
    print(f"   Rota: {' → '.join(parent1.rota_nomes())}")
    parent1.calcular_aptidao()
    print(f"   Distância: {parent1.aptidao:.2f} km")
    
    print("\n📍 Parent 2 (Progenitor 2):")
    print(f"   Rota: {' → '.join(parent2.rota_nomes())}")
    parent2.calcular_aptidao()
    print(f"   Distância: {parent2.aptidao:.2f} km")
    
    # Fazer o cruzamento
    filho = cruzamento_ox(parent1, parent2, partida)
    
    print("\n👶 Filho (resultado do cruzamento OX):")
    print(f"   Rota: {' → '.join(filho.rota_nomes())}")
    filho.calcular_aptidao()
    print(f"   Distância: {filho.aptidao:.2f} km")
    
    # Validação: verificar se o filho é válido
    ids_pai1 = {c.id for c in parent1.cromossomo}
    ids_pai2 = {c.id for c in parent2.cromossomo}
    ids_filho = {c.id for c in filho.cromossomo}
    
    print("\n✓ Validação:")
    print(f"   Cidades no pai 1: {sorted(ids_pai1)}")
    print(f"   Cidades no pai 2: {sorted(ids_pai2)}")
    print(f"   Cidades no filho: {sorted(ids_filho)}")
    print(f"   Filho começa com partida? {filho.cromossomo[0].id == partida.id}")
    print(f"   Filho tem mesmo número de cidades? {len(ids_filho) == len(ids_pai1)}")
    print(f"   Todas as cidades do filho estão nos pais? {ids_filho == ids_pai1}")
 
 
# =============================================================================
# TESTE 2: Mutação Simples (Swap)
# =============================================================================
 
def teste_mutacao_simples():
    """Testa o operador de mutação simples por swap."""
    print("\n" + "="*80)
    print("TESTE 2: MUTAÇÃO SIMPLES (SWAP DE DUAS CIDADES ADJACENTES)")
    print("="*80)
    
    cidades = popular_cidades()
    partida = cidades[0]
    
    # Criar um indivíduo
    individuo = gerar_individuo_aleatorio(partida, cidades)
    individuo.calcular_aptidao()

    print("\n🧬 Indivíduo original:")
    print(f"   Rota: {' → '.join(individuo.rota_nomes())}")
    print(f"   Distância: {individuo.aptidao:.2f} km")

    # Aplicar mutação com alta probabilidade para garantir que ocorra
    print("\n🔄 Aplicando mutação (probabilidade = 100%)...")
    individuo_mutado = mutacao_simples(individuo, probabilidade_mutacao=1.0)
    individuo_mutado.calcular_aptidao()
    
    print("\n🧬 Indivíduo mutado:")
    print(f"   Rota: {' → '.join(individuo_mutado.rota_nomes())}")
    print(f"   Distância: {individuo_mutado.aptidao:.2f} km")
    
    # Mostrar a diferença
    print("\n📊 Comparação:")
    print(f"   Melhoria: {individuo.aptidao - individuo_mutado.aptidao:.2f} km")
    if individuo_mutado.aptidao < individuo.aptidao:
        print("   ✓ A mutação melhorou a solução!")
    elif individuo_mutado.aptidao == individuo.aptidao:
        print("   ≈ A mutação não alterou a aptidão")
    else:
        print("   ✗ A mutação piorou a solução")
 
 
# =============================================================================
# TESTE 3: Mutação por Inversão
# =============================================================================
 
def teste_mutacao_inversao():
    """Testa o operador de mutação por inversão de segmento."""
    print("\n" + "="*80)
    print("TESTE 3: MUTAÇÃO POR INVERSÃO DE SEGMENTO")
    print("="*80)
    
    cidades = popular_cidades()
    partida = cidades[0]
    
    # Criar um indivíduo
    individuo = gerar_individuo_aleatorio(partida, cidades)
    individuo.calcular_aptidao()

    print("\n🧬 Indivíduo original:")
    print(f"   Rota: {' → '.join(individuo.rota_nomes())}")
    print(f"   Distância: {individuo.aptidao:.2f} km")

    # Aplicar mutação com alta probabilidade
    print("\n🔄 Aplicando mutação por inversão (probabilidade = 100%)...")
    individuo_mutado = mutacao_inversao(individuo, probabilidade_mutacao=1.0)
    individuo_mutado.calcular_aptidao()
    
    print("\n🧬 Indivíduo mutado:")
    print(f"   Rota: {' → '.join(individuo_mutado.rota_nomes())}")
    print(f"   Distância: {individuo_mutado.aptidao:.2f} km")
    
    # Mostrar a diferença
    print("\n📊 Comparação:")
    print(f"   Melhoria: {individuo.aptidao - individuo_mutado.aptidao:.2f} km")
    if individuo_mutado.aptidao < individuo.aptidao:
        print("   ✓ A mutação melhorou a solução!")
    elif individuo_mutado.aptidao == individuo.aptidao:
        print("   ≈ A mutação não alterou a aptidão")
    else:
        print("   ✗ A mutação piorou a solução")
 
 
# =============================================================================
# TESTE 4: Probabilidades realistas
# =============================================================================
 
def teste_probabilidades():
    """Testa mutação com probabilidades realistas."""
    print("\n" + "="*80)
    print("TESTE 4: PROBABILIDADES REALISTAS")
    print("="*80)
    
    cidades = popular_cidades()
    partida = cidades[0]
    
    print("\n📊 Executando 100 mutações com probabilidade = 10%:")
    print("(Esperado: ~10 mutações ocorrem)\n")
    
    contador_mutacoes = 0
    
    for i in range(100):
        individuo = gerar_individuo_aleatorio(partida, cidades)
        individuo_mutado = mutacao_simples(individuo, probabilidade_mutacao=0.1)
        
        # Verificar se houve mutação
        if individuo_mutado.cromossomo != individuo.cromossomo:
            contador_mutacoes += 1
    
    print(f"Mutações ocorridas: {contador_mutacoes}/100 ({contador_mutacoes}%)")
    print(f"Taxa esperada: ~10%")
    
    if 5 <= contador_mutacoes <= 15:
        print("✓ Resultado dentro do esperado!")
    else:
        print("⚠ Resultado fora do esperado (isso pode acontecer por chance)")
 
 
# =============================================================================
# TESTE 5: Integração com loop de épocas
# =============================================================================
 
def teste_integracao_loop():
    """Exemplo de como usar os operadores em um loop de gerações."""
    print("\n" + "="*80)
    print("TESTE 5: INTEGRAÇÃO COM LOOP DE ÉPOCAS")
    print("="*80)
    
    from algoritmos_geneticos import gerar_populacao_aleatoria, seleciona_melhores_individuos
    
    cidades = popular_cidades()
    partida = cidades[0]
    
    print("\n🏁 Simulando 5 épocas com crossover e mutação:\n")
    
    # Gerar população inicial
    tamanho_populacao = 100
    numero_epocas = 5
    
    populacao = gerar_populacao_aleatoria(tamanho_populacao, partida, cidades)
    
    # Calcular aptidão inicial
    for ind in populacao:
        ind.calcular_aptidao()
    
    melhor_global = min(populacao, key=lambda x: x.aptidao)
    
    print(f"{'ÉPOCA':<8} {'MELHOR':<15} {'MÉDIA':<15}")
    print("-" * 40)
    
    # Loop de épocas
    for epoca in range(numero_epocas):
        # Calcular estatísticas
        aptidoes = [ind.aptidao for ind in populacao]
        melhor = min(aptidoes)
        media = sum(aptidoes) / len(aptidoes)
        
        if melhor < melhor_global.aptidao:
            melhor_global = min(populacao, key=lambda x: x.aptidao)
        
        print(f"{epoca+1:<8} {melhor_global.aptidao:<15.2f} {media:<15.2f}")
        
        # Seleção (elitismo)
        melhores = seleciona_melhores_individuos(populacao, 3)
        
        # Criar nova população com crossover e mutação
        nova_populacao = []
        
        # Manter os melhores (elitismo)
        nova_populacao.extend(melhores)
        
        # Gerar novos indivíduos via crossover e mutação
        while len(nova_populacao) < tamanho_populacao:
            # Selecionar dois pais aleatoriamente
            pai1 = melhores[0]
            pai2 = melhores[1] if len(melhores) > 1 else melhores[0]
            
            # Fazer crossover
            filho = cruzamento_ox(pai1, pai2, partida)
            
            # Aplicar mutação
            filho = mutacao_simples(filho, probabilidade_mutacao=0.1)
            
            # Calcular aptidão
            filho.calcular_aptidao()
            
            nova_populacao.append(filho)
        
        populacao = nova_populacao[:tamanho_populacao]
    
    melhor_global.calcular_aptidao()
    print("\n" + "="*40)
    print(f"✓ Melhor solução encontrada: {melhor_global.distancia:.2f} km")
    print(f"Rota: {' → '.join(melhor_global.rota_nomes())}")
 
# =============================================================================
# Gráfico de convergência
# =============================================================================

def plotar_convergencia(
    historico_distancias: list[float],
    historico_aptidoes: list[float],
    caminho_arquivo: str = "convergencia.png",
) -> None:
    """
    Plota a evolução do melhor indivíduo por época.

    Parâmetros
    ----------
    historico_distancias : list[float]
        Distância real (sem penalidade) do melhor indivíduo em cada época.
    historico_aptidoes : list[float]
        Aptidão (distância + penalidade) do melhor indivíduo em cada época.
    caminho_arquivo : str
        Caminho do arquivo PNG gerado (padrão: convergencia.png).
    """
    epocas = list(range(1, len(historico_distancias) + 1))

    _, ax = plt.subplots(figsize=(10, 5))
    ax.plot(epocas, historico_distancias, marker="o", label="Distância real (km)")
    ax.plot(epocas, historico_aptidoes,   marker="s", label="Aptidão (km + penalidade)")
    ax.set_xlabel("Época")
    ax.set_ylabel("Valor (km)")
    ax.set_title("Convergência do Algoritmo Genético")
    ax.legend()
    ax.grid(True)

    plt.tight_layout()
    plt.savefig(caminho_arquivo)
    print(f"\nGráfico salvo em: {caminho_arquivo}")
    plt.show()


# =============================================================================
# Mapa interativo da rota
# =============================================================================

def plotar_rota_mapa(
    individuo: Individuo,
    caminho_arquivo: str = "rota.html",
) -> None:
    """
    Gera um mapa interativo HTML com a melhor rota encontrada.

    Cores dos marcadores
    --------------------
    Verde  — cidade de partida/chegada (sem produto)
    Vermelho — prioridade 1 (vacinas / medicamentos)
    Azul     — prioridade 2 (insumos)

    Parâmetros
    ----------
    individuo : Individuo
        Indivíduo com cromossomo e aptidão já calculada.
    caminho_arquivo : str
        Caminho do arquivo HTML gerado (padrão: rota.html).
    """
    cidades_rota = individuo.cromossomo
    coords = [(c.latitude, c.longitude) for c in cidades_rota]

    lats = [c.latitude  for c in cidades_rota[:-1]]
    lons = [c.longitude for c in cidades_rota[:-1]]
    centro = (sum(lats) / len(lats), sum(lons) / len(lons))

    mapa = folium.Map(location=centro, zoom_start=7)

    folium.PolyLine(coords, color="darkblue", weight=2.5, opacity=0.8).add_to(mapa)

    for ordem, cidade in enumerate(cidades_rota[:-1], start=1):
        if cidade.produto is None:
            cor, icone = "green", "home"
            popup_html = f"<b>#{ordem} {cidade.nome}</b><br>Partida / Chegada"
        elif cidade.produto.prioridade == 1:
            cor, icone = "red", "plus"
            popup_html = (
                f"<b>#{ordem} {cidade.nome}</b><br>"
                f"{cidade.produto.nome}<br>"
                f"Prioridade: Alta (1)"
            )
        else:
            cor, icone = "blue", "info-sign"
            popup_html = (
                f"<b>#{ordem} {cidade.nome}</b><br>"
                f"{cidade.produto.nome}<br>"
                f"Prioridade: Baixa (2)"
            )

        folium.Marker(
            location=(cidade.latitude, cidade.longitude),
            popup=folium.Popup(popup_html, max_width=200),
            tooltip=f"#{ordem} {cidade.nome}",
            icon=folium.Icon(color=cor, icon=icone),
        ).add_to(mapa)

    mapa.save(caminho_arquivo)
    print(f"Mapa salvo em: {caminho_arquivo}")


 # =============================================================================
# DEMONSTRAÇÃO DE USO
# =============================================================================

if __name__ == "__main__":

    # Algumas cidades do estado de São Paulo
    cidades = popular_cidades()

    # Cidade de partida
    partida = cidades[0] # São Paulo
        
    print("\n=== Distâncias a partir de São Paulo ===")
    sp = cidades[0]
    for outra in cidades[1:]:
        print(f"  {sp.nome} → {outra.nome}: {sp.distancia_para(outra):.1f} km")

    print("\n=== Matriz de distâncias (KM) ===")
    matriz = gerar_matriz_distancias(cidades)
    

    print("\n=== CRIANDO INDIVIDUOS ===")

    tamanho_populacao=100
    # --- Cria 10 indivíduos com rota aleatória ---
    populacao_inicial = gerar_populacao_aleatoria(tamanho_populacao, partida, cidades)
    
   # melhores_individuos = seleciona_melhores_individuos(populacao_inicial, 5)
    
    numero_epocas=1000
    quantidade_elite=3
    

    melhor_individuo_global = None
    historico_distancias: list[float] = []
    historico_aptidoes: list[float] = []

    for epoca in range(numero_epocas):
        # Selecionar melhores (elitismo)
        melhores = seleciona_melhores_individuos(populacao_inicial, quantidade_elite)

        # Criar nova população
        populacao_nova = gerar_populacao_aleatoria(tamanho_populacao, partida, cidades, melhores)

        # Atualizar melhor indivíduo global
        melhor_atual = min(populacao_nova, key=lambda ind: ind.calcular_aptidao())
        if melhor_individuo_global is None or melhor_atual.calcular_aptidao() < melhor_individuo_global.calcular_aptidao():
            melhor_individuo_global = melhor_atual

        historico_distancias.append(melhor_atual.distancia)
        historico_aptidoes.append(melhor_atual.aptidao)

        populacao_inicial = populacao_nova

    plotar_convergencia(historico_distancias, historico_aptidoes)
    plotar_rota_mapa(melhor_individuo_global)

    melhor_individuo_global.calcular_aptidao()
    print("\n=== Melhor indivíduo encontrado ===")
    for cidade in melhor_individuo_global.cromossomo:
        prioridade = f" [{cidade.produto.prioridade}]" if cidade.produto else ""
        print(f"  {cidade.nome}{prioridade}")
    print(f"Distância real percorrida : {melhor_individuo_global.distancia:.2f} km")
    print(f"Violacoes de prioridade   : {int((melhor_individuo_global.aptidao - melhor_individuo_global.distancia) / Individuo._PENALIDADE_POR_VIOLACAO)}")



    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "TESTES DOS OPERADORES GENÉTICOS (CROSSOVER E MUTAÇÃO)".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    teste_crossover()
    teste_mutacao_simples()
    teste_mutacao_inversao()
    teste_probabilidades()
    teste_integracao_loop()
    
    print("\n" + "="*80)
    print("✓ TODOS OS TESTES CONCLUÍDOS!")
    print("="*80 + "\n")