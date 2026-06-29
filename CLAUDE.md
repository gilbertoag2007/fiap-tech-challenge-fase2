# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Escopo de Trabalho

**Nunca leia ou altere arquivos fora da pasta `api-rotas-medicas/`.** Os demais diretórios do repositório (`poc/`, `codigo_base_professor/` e arquivos na raiz) são referência do professor e protótipo anterior — apenas leitura quando necessário para entender a lógica, mas sem edição.

---

## Objetivo

API FastAPI que resolve o TSP (Travelling Salesman Problem) aplicado a rotas de entrega de medicamentos e insumos via Algoritmos Genéticos. Recebe uma lista de códigos IBGE de municípios com o respectivo produto e prioridade, e retorna a rota otimizada.

---

## Comandos

```bash
# Dentro de api-rotas-medicas/
uvicorn main:app --reload

# Instalar dependências
pip install fastapi uvicorn pydantic
```

---

## Arquitetura de `api-rotas-medicas/`

```
api-rotas-medicas/
├── main.py                        # Entrypoint FastAPI (template incorreto — precisa ser reescrito)
├── api/
│   ├── routers/                   # Routers FastAPI (apenas __init__.py, a construir)
│   └── schemas/                   # Schemas Pydantic request/response (vazio, a construir)
├── models/
│   ├── cidade.py                  # Classe Cidade com Haversine
│   ├── Individuo.py               # Cromossomo / solução candidata
│   └── produto.py                 # Classe Produto (tem bug de indentação)
├── services/
│   └── algoritmos_geneticos.py    # Operadores genéticos (desatualizado — usa .id em vez de .cod_ibge)
└── config/
    └── settings.py                # Settings via .env (template de outro projeto — precisa ser limpo)
```

### Problemas conhecidos que precisam ser corrigidos

| Arquivo | Problema |
|---------|----------|
| `main.py` | Conteúdo de outro projeto (ANP RAG). Precisa ser substituído pelo entrypoint de rotas médicas. |
| `services/algoritmos_geneticos.py` | Usa `c.id` e `partida.id`, mas `models/cidade.py` usa `cod_ibge`. Atualizar para `cod_ibge`. |
| `models/produto.py` | `__eq__`, `__hash__`, `__repr__`, `__str__` estão no nível do módulo, fora da classe. |
| `config/settings.py` | Tem variáveis de OpenAI e banco Oracle. Substituir pelas variáveis reais da aplicação. |

---

## Classes de Domínio (`models/`)

### `Cidade`
- Identificador canônico: `cod_ibge: int` (código IBGE do município)
- Possui `regiao_tradicional: str | None` para restrição de agrupamento regional
- `distancia_para(outra)` — fórmula Haversine, **nunca modificar**
- `RAIO_TERRA_KM = 6371.0` constante de classe
- `produto: Produto | None` — a cidade de partida tem `produto=None`

### `Individuo`
- `cromossomo: list[Cidade]` — sempre `[partida, c1, c2, ..., partida]` (rota circular)
- `calcular_aptidao()` define `self.distancia` e `self.aptidao` como efeito colateral; acesse-os somente após chamar esse método
- `_PENALIDADE_POR_VIOLACAO = 10_000.0` por par de cidades fora de ordem de prioridade
- Toda nova restrição TSP segue o padrão: adicionar método `_penalidade_X()` e somá-lo em `calcular_aptidao()`
- **Sem lógica genética nesta classe**

### `Produto`
- `prioridade: int` — `1` = alta urgência (vacinas/medicamentos), `2` = baixa urgência (insumos)
- Validação no `__init__`: `prioridade not in {1, 2}` lança `ValueError`

### `services/algoritmos_geneticos.py`
- `gerar_individuo_aleatorio(partida, cidades)` → `[partida] + shuffle(demais) + [partida]`
- `gerar_populacao_aleatoria(quantidade, partida, cidades, melhores_individuos=None)` — elitismo via parâmetro opcional
- `seleciona_melhores_individuos(populacao, quantidade)` — ordena por `calcular_aptidao()` ascendente
- `cruzamento_ox(parent1, parent2, partida)` — Order Crossover
- `mutacao_simples(individuo, probabilidade)` — swap de duas cidades adjacentes internas
- `mutacao_inversao(individuo, probabilidade)` — inversão de segmento interno

---

## Invariantes Críticos

1. `cromossomo[0] == cromossomo[-1] == partida` — sempre, sem exceção
2. `cromossomo[1:-1]` não contém duplicatas nem a cidade de partida
3. `calcular_aptidao()` deve ser chamado antes de acessar `individuo.distancia` ou `individuo.aptidao`
4. `cromossomo` é sempre `list[Cidade]`, nunca string ou tuple
5. Lógica genética pertence a `services/algoritmos_geneticos.py`, não a `Individuo`

---

## Convenções de Código

- Docstrings estilo NumPy (`Parâmetros / Retorna / Notas`)
- Type hints em todos os métodos
- Listas no plural: `populacao`, `cidades`, `melhores`
- Métodos privados de penalidade: prefixo `_penalidade_` (ex: `_penalidade_prioridade()`)
- Proibido abreviar: `calcular_aptidao()` não `calc_apt()`