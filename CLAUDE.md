# CLAUDE.md

Este arquivo orienta o Claude Code ao trabalhar neste repositório.

## Escopo de Trabalho

**Leia e altere apenas arquivos dentro de `api-rotas-medicas/` e `frontend-rotas-medicas/`.** Os demais diretórios (`poc/`, `codigo_base_professor/` e arquivos na raiz) são referência do professor e protótipo anterior — consulte-os apenas para entender a lógica original, sem edição.

---

## Objetivo

Sistema composto por uma API FastAPI (backend) e um frontend React, que resolve o TSP (Problema do Caixeiro Viajante) aplicado a rotas de entrega de medicamentos e insumos usando Algoritmos Genéticos. O usuário descreve a rota em linguagem natural; a API interpreta via ChatGPT (function calling) e retorna a rota otimizada como GeoJSON; o frontend exibe o resultado em um mapa interativo Leaflet.

---

## Comandos

```bash
# --- Backend (api-rotas-medicas/) ---
pip install fastapi uvicorn pydantic openai python-dotenv
uvicorn main:app --reload          # sobe em http://localhost:8000

# --- Frontend (frontend-rotas-medicas/) ---
npm install                        # instalar dependências (apenas na primeira vez)
npm run dev                        # sobe em http://localhost:5173
npm run build                      # gera build de produção em dist/
```

### Variáveis de ambiente (`.env` na raiz de `api-rotas-medicas/`)

```
OPENAI_API_KEY=<sua-chave>
MODELO_CHAT=gpt-4.1-nano
```

---

## Arquitetura de `api-rotas-medicas/`

```
api-rotas-medicas/
├── main.py                          # Entrypoint FastAPI — routers e CORS configurados
├── .env                             # Variáveis de ambiente (não commitar)
├── .env.example                     # Modelo do .env sem valores reais
├── api/
│   ├── routers/
│   │   ├── cidade.py                # GET /cidades/ — consulta de municípios do IBGE
│   │   ├── produto.py               # GET /produtos/ — consulta de produtos cadastrados
│   │   └── rotas.py                 # POST /rotas/ — executa o AG e retorna GeoJSON
│   └── schemas/
│       ├── cidade.py                # CidadeResponse (Pydantic)
│       ├── produto.py               # ProdutoResponse (Pydantic)
│       └── rotas.py                 # RotasRequest (Pydantic) com validações
├── models/
│   ├── cidade.py                    # Classe Cidade com Haversine
│   ├── Individuo.py                 # Cromossomo / solução candidata do AG
│   └── produto.py                   # Classe Produto com prioridade de entrega
├── services/
│   ├── algoritmos_geneticos.py      # Operadores genéticos (população, crossover, mutação)
│   ├── cidade_service.py            # Singleton — carrega CSV do IBGE, consultas e montagem de rotas
│   ├── produto_service.py           # Singleton — carrega CSV de produtos, consultas
│   ├── llm_service.py               # Interpreta mensagem via ChatGPT (function calling)
│   └── rota_service.py              # Orquestra LLM → AG → GeoJSON
├── data/
│   ├── cidades.csv                  # Municípios brasileiros (IBGE): COD_IBGE, NOME, UF, LATITUDE, LONGITUDE, REGIAO_TRADICIONAL
│   └── produtos.csv                 # Produtos: ID, NOME, PRIORIDADE
└── config/
    └── settings.py                  # Lê .env via python-dotenv; expõe OPENAI_API_KEY e MODELO_RESPOSTA
```

---

## Arquitetura de `frontend-rotas-medicas/`

```
frontend-rotas-medicas/
├── index.html                       # Entrypoint HTML — carrega Inter font e o bundle React
├── package.json                     # Dependências: react, react-dom, leaflet
├── vite.config.js                   # Proxy /rotas /cidades /produtos /health → localhost:8000
├── tailwind.config.js               # Configuração do Tailwind CSS
├── postcss.config.js                # PostCSS (Tailwind + Autoprefixer)
└── src/
    ├── main.jsx                     # Bootstrap React — importa leaflet.css e index.css
    ├── index.css                    # Tailwind directives + estilos globais + scrollbar
    ├── App.jsx                      # Layout raiz: sidebar + painel de formulário + painel de mapa
    └── components/
        ├── Sidebar.jsx              # Sidebar escura com logo e navegação
        ├── RouteForm.jsx            # Formulário com todos os parâmetros do RotasRequest
        ├── MapView.jsx              # Mapa Leaflet com marcadores numerados e polilinha da rota
        └── MedicalIllustration.jsx  # SVG ilustrativo exibido antes de gerar a rota
```

### Stack do frontend

| Camada | Tecnologia |
|---|---|
| Framework | React 18 + Vite 5 |
| Estilo | Tailwind CSS 3 |
| Mapa | Leaflet.js (vanilla, sem react-leaflet) |
| HTTP | `fetch` nativo com proxy Vite |
| Ícones | SVGs inline |

### Fluxo do frontend

```
Usuário preenche RouteForm
    │  POST /rotas/ (proxy Vite → localhost:8000)
    ▼
App.jsx recebe GeoJSON FeatureCollection
    │  passa geoJson para MapView
    ▼
MapView renderiza:
    - Marcadores numerados (vermelho = prioridade 1, azul = prioridade 2)
    - Polilinha tracejada conectando as cidades na ordem de visita
    - Popup por cidade: nome, UF, produto, prioridade
    - Legenda no canto inferior esquerdo
```

---

## Endpoints

### `POST /rotas/`
Ponto central da API. Recebe a descrição textual da rota e os parâmetros do AG.

**Request body (`RotasRequest`):**

| Campo | Tipo | Restrições | Descrição |
|---|---|---|---|
| `mensagem` | str | 20–200 chars | Descrição em linguagem natural da rota e produtos |
| `epocas` | int | 1–100.000 | Número de gerações do AG |
| `elitismo` | int | 0 ou 1 | 1 = preserva os melhores a cada geração |
| `grau_mutacao` | float | 0.0–10.0 | Taxa de mutação em % (dividida por 100 internamente) |
| `populacao_apenas_aleatoria` | int | 0 ou 1 | Reservado para extensões futuras |
| `tamanho_populacao` | int | 1–10.000 | Número de indivíduos na população |
| `tamanho_elite` | int | ≥ 1, < `tamanho_populacao` | Indivíduos preservados por elitismo |

**Resposta:** GeoJSON `FeatureCollection` com uma `Feature` do tipo `Point` por cidade (na ordem de visita), contendo: `ordem_visita`, `cidade`, `uf`, `regiao_tradicional`, `produto`, `prioridade`.

### `GET /cidades/`
Lista todos os municípios. Filtros disponíveis:
- `GET /cidades/{cod_ibge}` — busca por código IBGE
- `GET /cidades/pesquisar?termo=` — busca por fragmento de nome
- `GET /cidades/uf/{uf}` — filtra por estado (ex.: `RJ`)
- `GET /cidades/regiao/{regiao}` — filtra por região tradicional

### `GET /produtos/`
Lista todos os produtos. Filtros:
- `GET /produtos/{id}` — busca por ID
- `GET /produtos/pesquisar?termo=` — busca por fragmento de nome

### `GET /health`
Verifica se a API está operacional.

---

## Fluxo de execução de `POST /rotas/`

```
RotasRequest
    │
    ▼
LLMService.interpretar_mensagem(mensagem)
    │  ChatGPT com function calling pesquisa cidades e produtos nos services locais
    │  Retorna: list[{"cod_ibge": int, "produto_id": int}]
    │
    ▼
CidadeService.montar_cidades_com_produtos(pares)
    │  Retorna: list[Cidade] com produto preenchido
    │
    ▼
ag.gerar_populacao_aleatoria(tamanho_populacao, partida, cidades)
    │  Tamanho é ajustado automaticamente para min(tamanho_populacao, (N-1)!)
    │
    ▼
Loop por `epocas` gerações:
    │  seleciona_melhores_individuos → cruzamento_ox → mutacao_simples → mutacao_inversao
    │
    ▼
melhor Individuo → GeoJSON FeatureCollection
```

---

## Classes de Domínio (`models/`)

### `Cidade`
- Identificador canônico: `cod_ibge: int`
- `regiao_tradicional: str | None` — campo do CSV do IBGE para filtro regional
- `produto: Produto | None` — a cidade de partida tem `produto=None`
- `distancia_para(outra)` — fórmula de Haversine; **nunca modificar**
- `RAIO_TERRA_KM = 6371.0` — constante de classe
- `__eq__` e `__hash__` baseados em `cod_ibge`

### `Individuo`
- `cromossomo: list[Cidade]` — sempre `[partida, c1, c2, ..., partida]` (rota circular)
- `calcular_aptidao()` — define `self.distancia` e `self.aptidao` como efeito colateral; acesse-os **somente após** chamar esse método
- `_PENALIDADE_POR_VIOLACAO = 10_000.0` por par de cidades fora de ordem de prioridade
- Toda nova restrição TSP segue o padrão: adicionar método `_penalidade_X()` e somá-lo em `calcular_aptidao()`
- `is_valido()` — verifica integridade do cromossomo
- `rota_nomes()` — retorna lista de nomes na ordem de visita
- **Sem lógica genética nesta classe**

### `Produto`
- `prioridade: int` — `1` = alta urgência (vacinas/medicamentos), `2` = baixa urgência (insumos)
- Validação no `__init__`: `prioridade not in {1, 2}` lança `ValueError`

---

## Services

### `CidadeService` (`cidade_service` — singleton)
- Carrega `data/cidades.csv` uma única vez na inicialização
- Coordenadas armazenadas como inteiros no CSV (ex.: `-119283`); convertidas para graus decimais via `_parse_coordenada()` com inferência automática do divisor
- `montar_cidades_com_produtos(pares)` — recebe lista de `{cod_ibge, produto_id}` e retorna novas instâncias de `Cidade` com produto atribuído

### `ProdutoService` (`produto_service` — singleton)
- Carrega `data/produtos.csv` uma única vez
- `pesquisar_por_nome(termo)` — busca bidirecional: o nome do produto está contido no termo **ou** o termo está contido no nome

### `LLMService`
- Usa a API OpenAI com **function calling** para interpretar a mensagem em linguagem natural
- Loop de tool calling até o modelo emitir resposta final (`finish_reason != "tool_calls"`)
- Ferramentas disponíveis para o modelo: `pesquisar_cidade_por_nome`, `listar_cidades_por_regiao`, `listar_cidades_por_uf`, `pesquisar_produto_por_nome`
- Retorna lista de `{"cod_ibge": int, "produto_id": int}`

### `RotaService`
- Orquestra: LLMService → CidadeService → AG → GeoJSON
- `grau_mutacao` recebido em % (0–10), convertido para probabilidade (0.0–1.0) antes de chamar os operadores
- Imprime progresso a cada 10% das épocas no stdout

### `services/algoritmos_geneticos.py`
- `gerar_individuo_aleatorio(partida, cidades)` → `[partida] + shuffle(demais) + [partida]`
- `gerar_populacao_aleatoria(quantidade, partida, cidades, melhores_individuos=None)` — ajusta `quantidade` automaticamente para `min(quantidade, (N-1)!)` quando o número de cidades é pequeno; elitismo via parâmetro opcional
- `seleciona_melhores_individuos(populacao, quantidade)` — ordena por `calcular_aptidao()` ascendente
- `cruzamento_ox(parent1, parent2, partida)` — Order Crossover (OX)
- `mutacao_simples(individuo, probabilidade)` — swap de duas cidades adjacentes internas
- `mutacao_inversao(individuo, probabilidade)` — inversão de segmento interno

---

## Invariantes Críticos

1. `cromossomo[0] == cromossomo[-1] == partida` — sempre, sem exceção
2. `cromossomo[1:-1]` não contém duplicatas nem a cidade de partida
3. `calcular_aptidao()` deve ser chamado antes de acessar `individuo.distancia` ou `individuo.aptidao`
4. `cromossomo` é sempre `list[Cidade]`, nunca string ou tuple
5. Lógica genética pertence a `services/algoritmos_geneticos.py`, não a `Individuo`
6. O `.env` **nunca deve ser commitado** — use `.env.example` como referência

---

## Convenções de Código

- Docstrings estilo NumPy (`Parâmetros / Retorna / Notas`)
- Type hints em todos os métodos
- Listas no plural: `populacao`, `cidades`, `melhores`
- Métodos privados de penalidade: prefixo `_penalidade_` (ex.: `_penalidade_prioridade()`)
- Proibido abreviar: `calcular_aptidao()` não `calc_apt()`
- Singletons dos services importados diretamente: `from services.cidade_service import cidade_service`