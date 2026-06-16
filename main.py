from Individuo import Individuo
from cidade import Cidade
from utils import gerar_matriz_distancias


# =============================================================================
# DEMONSTRAÇÃO DE USO
# =============================================================================

if __name__ == "__main__":

    # Algumas cidades do estado de São Paulo
    cidades = [
        Cidade(0, "São Paulo",           "SP", -23.5505, -46.6333),
        Cidade(1, "Campinas",            "SP", -22.9056, -47.0608),
        Cidade(2, "Ribeirão Preto",      "SP", -21.1775, -47.8103),
        Cidade(3, "Santos",              "SP", -23.9618, -46.3322),
        Cidade(4, "Sorocaba",            "SP", -23.5015, -47.4526),
        Cidade(5, "São José dos Campos", "SP", -23.1794, -45.8869),
    ]

    print("=== Cidades cadastradas ===")
    for c in cidades:
        print(f"  {c}")

    print("\n=== Distâncias a partir de São Paulo ===")
    sp = cidades[0]
    for outra in cidades[1:]:
        print(f"  {sp.nome} → {outra.nome}: {sp.distancia_para(outra):.1f} km")

    print("\n=== Matriz de distâncias (KM) ===")
    matriz = gerar_matriz_distancias(cidades)
    header = f"{'':22}" + "".join(f"{c.nome[:10]:>12}" for c in cidades)
    print(header)
    for i, c in enumerate(cidades):
        linha = f"  {c.nome:<20}" + "".join(f"{matriz[i][j]:>12.1f}" for j in range(len(cidades)))
        print(linha)

    print("\n=== CRIANDO INDIVIDUOS ===")

   # --- Cria dois indivíduos com rota aleatória ---
    pais = [Individuo(cidades) for _ in range(10)]

    melhor = None

    for individuo in pais:
        individuo.calcular_aptidao()
        print(f"Indivíduo: {individuo} | Válido: {individuo.is_valido()} | Distância: {individuo.aptidao:.1f} km")
        if melhor is None or individuo.aptidao < melhor.aptidao:
            melhor = individuo

    print(f"Melhor indivíduo (menor distância): {melhor.aptidao:.1f} km | Rota: {' → '.join(melhor.rota_nomes())}")

   # print("=== Pais ===")
   # print(f"Pai 1: {pai1}")
   # print(f"Pai 2: {pai2}")

    # --- Cruzamento OX ---
    #filho1, filho2 = pai1.cruzamento_ox(pai2)
    #filho1.calcular_aptidao()
    #filho2.calcular_aptidao()

    #print("\n=== Filhos após Cruzamento OX ===")
    #print(f"Filho 1: {filho1} | válido: {filho1.is_valido()}")
    #print(f"Filho 2: {filho2} | válido: {filho2.is_valido()}")

    # --- Mutação por inversão (forçada para demo) ---
    #filho1.mutacao_inversao(taxa_mutacao=1.0)
    #filho1.calcular_aptidao()
    #print(f"\nFilho 1 após mutação por inversão: {filho1}")

    # --- Ranking da população ---
    #populacao = [pai1, pai2, filho1, filho2]
    #populacao.sort()

  #  print("\n=== Ranking (menor distância = melhor) ===")
  #  for rank, ind in enumerate(populacao, 1):
  #      rota = " → ".join(ind.rota_nomes())
  #      print(f"  {rank}º {ind.aptidao:.1f} km | {rota}")
