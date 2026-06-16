
# =============================================================================
# Função utilitária: gera a matriz de distâncias a partir de uma lista de cidades
# =============================================================================
 
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
    return matriz
