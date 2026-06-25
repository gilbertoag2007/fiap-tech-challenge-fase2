# Sistema de Otimização de Rotas - Guia para Claude

## 🎯 Visão Geral do Projeto

**Objetivo:** Implementar um Sistema de Otimização de Rotas via Algoritmos Genéticos
para resolver o Problema do Caixeiro Viajante (TSP) aplicado a rotas de entrega de medicamentos e insumos.

**Escopo:** Otimizar rotas nas cidades do estado de São Paulo (Brasil), minimizando distância total.

---

## 🏗️ Arquitetura e Estrutura de Classes

### Camadas do Sistema
┌─────────────────────────────┐

│   main.py (Orquestrador)    │

├─────────────────────────────┤

│  algoritmos_geneticos.py (AG)│  ← Operadores genéticos

├─────────────────────────────┤

│  individuo.py (Cromossomo)  │  ← Representação de solução

├─────────────────────────────┤

│ cidade.py (Dado geográfico) │

├─────────────────────────────┤

│   utils.py (Helpers)        │  ← População, helpers


### Classes Principais

#### **Cidade**
- **Responsabilidade:** Representar uma cidade com dados geográficos
- **Atributos:** `id`, `nome`, `uf`, `latitude`, `longitude`
- **Métodos essenciais:** `distancia_para(outra)` usando Haversine
- **NUNCA modificar:** Cálculo de distância geodésica (é fórmula padrão)

#### **Individuo**
- **Responsabilidade:** Cromossomo = solução candidata (rota)
- **Estrutura:** `cromossomo: list[Cidade]` (permutação de cidades)
- **Restrição crítica 1:** Sempre começa com cidade de partida no índice [0]
- **Restrição crítica 2:** Sempre terminar com cidade de partida no índice[0] para reproduzir uma rota circular onde começa e termina na mesma cidade.

- **Métodos:**
  - `gerar_cromossomo_aleatorio()` → embaralha cidades
  - `calcular_aptidao()` → retorna distância total respeitando a prioridade de entrega.
  - `is_valido()` → detecta IDs duplicados
- **IMPORTANTE:** Apenas dados + estrutura. Sem lógica genética aqui!

#### **AlgoritmoGenetico**
- **Responsabilidade:** Implementar operadores genéticos
- **Operadores implementados:**
  - `cruzamento_ox(pai1, pai2)` → Order Crossover
  - `mutacao_swap()` → Troca adjacente
  - `mutacao_inversao()` → Inverte segmento
- **IMPORTANTE:** Preservar sempre a cidade de partida em [0]

#### **utils.py** (READ-ONLY)
- `gerar_populacao_aleatoria()` → Cria população inicial com validação
- `gerar_matriz_distancias()` → Pré-calcula distâncias
- `seleciona_melhores_individuos()` → Elitismo

---

## 🔑 Princípios de Design

### 1. **Separação de Responsabilidades**
```python
# ✅ BOM: Lógica genética em AlgoritmoGenetico
filho = ag.cruzamento_ox(pai1, pai2, partida)

# ❌ RUIM: Lógica genética em Individuo
filho = pai1.cruzamento_ox(pai2)
```

### 2. **Validação de Cromossomo**
- Cidade de partida **SEMPRE** é o primeiro elemento [0]
- Sem IDs duplicados no cromossomo
- Todos os IDs das cidades presentes

### 3. **Imutabilidade de Entrada**
- Não modificar `Cidade` original
- Não modificar pais em `cruzamento_ox()`
- Sempre retornar novo `Individuo`

### 4. **Tipo de Dados Cromossomo**
```python
# Estrutura interna
cromossomo: list[Cidade]  # Sempre uma lista, nunca string ou tuple

# Validação de unicidade usa tuple de IDs:
tuple(c.id for c in individuo.cromossomo)
```

---

## 📐 Restrições Técnicas

### Distância
- Cálculo: **Haversine** (geodésico)
- Unidade: **Quilômetros (KM)**
- Raio da Terra: `6371.0 km` (constante em Cidade)

### População
- Geração: Sempre aleatória + validação de unicidade
- Elitismo: Manter N melhores indivíduos entre gerações
- Validação: Duplicatas detectadas via `set(tuple(IDs))`

### Cromossomo
- Comprimento: Sempre `len(cidades)`
- Primeira posição: Sempre `partida.id`
- Ordem: Permutação válida de todas as cidades

### Aptidão (Fitness)
- Definição: Distância total da rota (viagem de ida e volta)
- Cálculo: Soma de `distancia_para()` entre cidades consecutivas
- Fórmula: `Σ distancia(cidade[i], cidade[i+1 % n])`

---

## 🔄 Loop de Épocas (Esperado)

```python
for epoca in range(num_epocas):
    # 1. Seleção (elitismo)
    melhores = seleciona_melhores_individuos(populacao, elite_size)
    
    # 2. Criar nova população
    nova_populacao = gerar_populacao_aleatoria(
        tamanho, 
        partida, 
        cidades,
        melhores_individuos=melhores  # Elitismo
    )
    
    # 3. Calcular aptidão
    for ind in nova_populacao:
        ind.calcular_aptidao()
    
    # 4. Estatísticas (opcional)
    melhor = min(nova_populacao, key=lambda x: x.aptidao)
    
    populacao = nova_populacao
```

---

## 🎯 Convenções de Código

### Nomenclatura
```python
# Variáveis
populacao: list[Individuo]  # Sempre plural
partida: Cidade             # Cidade de saída
cromossomo: list[Cidade]    # Rota completa

# Métodos
calcular_aptidao()          # Calcula e retorna
gerar_populacao_aleatoria() # Cria nova
cruzamento_ox()             # Operador genético

# Avoid
calc_apt()                  # ❌ Abreviações
Pop                         # ❌ Maiúsculas para variáveis
```

### Docstrings
```python
def cruzamento_ox(pai1: Individuo, pai2: Individuo, partida: Cidade) -> Individuo:
    """
    Order Crossover (OX) - operador de cruzamento.
    
    Parâmetros
    ----------
    pai1 : Individuo
        Primeiro progenitor
    pai2 : Individuo
        Segundo progenitor
    partida : Cidade
        Cidade de partida (preservada em [0])
    
    Retorna
    -------
    Individuo
        Novo indivíduo (filho) com cromossomo OX
    """
```

### Type Hints
```python
# SEMPRE use type hints
def gerar_cromossomo_aleatorio(
    self, 
    partida: Cidade, 
    cidades: list[Cidade]
) -> list[Cidade]:
```

---

## 📊 Próximas Fases (Roadmap)

### Fase 2: Restrições Realistas
- [ ] Priorização de cidades (entrega urgente vs normal)
- [ ] Capacidade de veículo (peso máximo)
- [ ] Range de veículo (autonomia)
- [ ] Janela de tempo (horário de entrega)

### Fase 3: VRP (Vehicle Routing Problem)
- [ ] Múltiplos veículos
- [ ] Distribuição de rotas entre veículos
- [ ] Balanceamento de carga

### Fase 4: Otimizações
- [ ] 2-opt local search
- [ ] Simulated annealing
- [ ] Parallelização de população

---

## ⚙️ Como Claude Deve Trabalhar Neste Projeto

### ✅ Sempre Faça
- Preservar a cidade de partida em posição [0]
- Validar unicidade de cromossomo antes de retornar
- Usar type hints em todos os métodos
- Testar com `criar_cidades_teste()`
- Manter separação: Dados em `Individuo`, Lógica em `AlgoritmoGenetico`

### ❌ Nunca Faça
- Modificar classe `Cidade` (fórmula Haversine está correta)
- Alterar arquivo `utils.py` (é read-only)
- Usar cromossomo como string ou tuple (sempre `list[Cidade]`)
- Colocar lógica genética em `Individuo`
- Ignorar validação de duplicatas

### 🔧 Quando Implementar Novo Operador
1. Implemente em `AlgoritmoGenetico`
2. Garanta que retorna novo `Individuo`
3. Preserve partida em [0]
4. Escreva teste dedicado em `main.py`
5. Documente em docstring

---

## 📚 Referências de Teste

### Cidades de Teste
```python
cidades_teste = [
    Cidade(0, "São Paulo",           "SP", -23.5505, -46.6333),
    Cidade(1, "Campinas",            "SP", -22.9056, -47.0608),
    Cidade(2, "Ribeirão Preto",      "SP", -21.1775, -47.8103),
    Cidade(3, "Santos",              "SP", -23.9618, -46.3322),
    Cidade(4, "Sorocaba",            "SP", -23.5015, -47.4526),
    Cidade(5, "São José dos Campos", "SP", -23.1794, -45.8869)
]
partida = cidades_teste[0]  # São Paulo
```

### Distâncias Esperadas (Validação)
- SP → Campinas: ~95 km
- SP → Santos: ~75 km
- SP → Sorocaba: ~100 km

---

## 🚀 Workflow Recomendado com Claude Code

```bash
# 1. Revisar um operador
@AlgoritmoGenetico.py Review the cruzamento_ox function

# 2. Corrigir bug específico
@Individuo.py [seleção de linhas] Fix the validation logic

# 3. Adicionar novo operador
> Implement a new mutation operator in AlgoritmoGenetico

# 4. Refatorar função
@utils.py Optimize the duplicate detection in gerar_populacao_aleatoria
```

---

## 📞 Contexto Adicional

- **Linguagem:** Python 3.8+
- **Paradigma:** Orientado a Objetos (OOP)
- **Padrão Genético:** Algoritmo Genético Simples
- **Benchmark:** TSP com 6 cidades (expandir depois)
- **IDE:** VS Code + Claude Code Extension

---