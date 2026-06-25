
# Sistema de Otimização de Rotas (TSP)

## 📌 Problema
Resolver o Traveling Salesman Problem para otimizar rotas de entrega de vacinas, medicamentos e insumos médicos.

## 🎯 Objetivo
Implementar um Algoritmo Genético que encontre a rota com menor distância respeitando a ordem de prioridade dos produtos a serem entregues.

Esse projeto faz parte do trabalho de conclusão da fase 2 da pós-graduação FIAP - IA para Devs - Grupo 88. Integrantes:

- Gustavo Denobi.
- Gilberto Cunha.
- Thiago Garbulha.
- Vitor Arruda.


## 🏗️ Arquitetura
- `Cidade`: Representa uma cidade com coordenadas e a lista de produtos a serem entregues para ela.
- `Produto`: Representa um produto a ser entregue na rota.
- `Individuo`: Cromossomo (solução) = lista de cidades na ordem da rota começando e terminando na cidade de partida para reproduzir uma rota circular
- `AlgoritmoGenetico`: Operadores genéticos como crossover e mutação.
- `utils.py`: Geração de população e helpers

## 🚀 Como Usar
```bash
python main.py
```

## 📊 Restrições
- Todas os cromossomos (solução) devem começar e terminar sempre com mesma cidade para reproduzir uma rota circular.
- A mesma cidade não pode ser visitada mais de uma vez. 
- A distância entre as cidade deve ser calculada via Haversine.
- A  cidades com produtos prioritários devem ser visitadas primeiro.