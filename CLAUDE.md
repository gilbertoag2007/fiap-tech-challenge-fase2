# CLAUDE.md

Este arquivo orienta o Claude Code ao trabalhar neste repositório.

## Escopo de Trabalho

**Leia e altere apenas arquivos dentro de `api-rotas-medicas/` e `frontend-rotas-medicas/`.** Os demais diretórios (`poc/`, `codigo_base_professor/` e arquivos na raiz) são referência do professor e protótipo anterior — consulte-os apenas para entender a lógica original, sem edição.

---

## Objetivo

Sistema composto por uma API FastAPI (backend) e um frontend React, que resolve o TSP (Problema do Caixeiro Viajante) aplicado a rotas de entrega de medicamentos e insumos usando Algoritmos Genéticos. O usuário descreve a rota em linguagem natural; a API interpreta via ChatGPT (function calling) e retorna a rota otimizada como GeoJSON; o frontend exibe o resultado em um mapa interativo Leaflet e em um painel de análise com gráfico de evolução.

O AG é configurável pelo usuário: estratégia de seleção (truncamento/torneio), crossover (OX/ERX), mutação (swap/inversão/ambos/or-opt), inicialização da população (aleatória/vizinho mais próximo), elitismo, busca local 2-opt e parada antecipada.

---

## Comandos

```bash
# --- Backend (api-rotas-medicas/) ---
pip install fastapi uvicorn pydantic openai python-dotenv pytest
uvicorn main:app --reload          # sobe em http://localhost:8000
pytest tests/ -q                   # roda a suíte automatizada (services/algoritmos_geneticos.py)

# --- Frontend (frontend-rotas-medicas/) ---
npm install                        # instalar dependências (apenas na primeira vez)
npm run dev                        # sobe em http://localhost:5173
npm run build                      # gera build de produção em dist/
```

### Variáveis de ambiente (`.env` na raiz de `api-rotas-medicas/`)

```
OPENAI_API_KEY=<sua-chave>
MODELO_CHAT=gpt-4.1-mini
```

`MODELO_CHAT` deve ser um modelo com suporte a function calling. Evite tiers "nano": a interpretação de mensagens compostas (múltiplos blocos região+produto, cidades fronteiriças por conhecimento próprio) exige recall factual e seguimento de instruções melhores que o tier mais barato oferece.

---

## Arquitetura de `api-rotas-medicas/`

```
api-rotas-medicas/
├── main.py                          # Entrypoint FastAPI — router de rotas, CORS e GET /health
├── .env                             # Variáveis de ambiente (não commitar)
├── .env.example                     # Modelo do .env sem valores reais
├── teste_services.py                # Script manual de fumaça dos services (não é a suíte automatizada)
├── requeriments.txt                 # Dependências pip
├── api/
│   ├── routers/
│   │   └── rotas.py                 # POST /rotas/ — executa o AG e retorna GeoJSON
│   └── schemas/
│       └── rotas.py                 # RotasRequest (Pydantic) com validações
├── models/
│   ├── cidade.py                    # Classe Cidade com Haversine
│   ├── individuo.py                 # Cromossomo / solução candidata do AG
│   └── produto.py                   # Classe Produto com prioridade de entrega
├── services/
│   ├── algoritmos_geneticos.py      # Operadores genéticos (inicialização, seleção, crossover, mutação, busca local)
│   ├── cidade_service.py            # Singleton — carrega CSV do IBGE, consultas e montagem de rotas
│   ├── produto_service.py           # Singleton — carrega CSV de produtos, consultas
│   ├── llm_service.py               # Interpreta mensagem via ChatGPT (function calling)
│   └── rota_service.py              # Orquestra LLM → AG → GeoJSON
├── tests/
│   └── test_algoritmos_geneticos.py # Suíte pytest: unitários + integração combinatória (seleção x init x mutação x elitismo)
├── data/
│   ├── cidades.csv                  # Municípios brasileiros (IBGE): COD_IBGE, NOME, UF, LATITUDE, LONGITUDE, REGIAO_TRADICIONAL
│   └── produtos.csv                 # Produtos: ID, NOME, PRIORIDADE
└── config/
    └── settings.py                  # Lê .env via python-dotenv; expõe OPENAI_API_KEY e MODELO_RESPOSTA
```

> Os endpoints `GET /cidades/` e `GET /produtos/` (e seus schemas `CidadeResponse`/`ProdutoResponse`) foram removidos por não serem consumidos pelo frontend nem por nenhum outro ponto da API — as consultas equivalentes continuam disponíveis internamente via `cidade_service`/`produto_service`, usadas pelo `LLMService` (function calling) e pelo `RotaService`.

---

## Arquitetura de `frontend-rotas-medicas/`

```
frontend-rotas-medicas/
├── index.html                       # Entrypoint HTML — carrega Inter font e o bundle React
├── package.json                     # Dependências: react, react-dom, leaflet, chart.js
├── vite.config.js                   # Proxy /rotas /health → localhost:8000
├── tailwind.config.js               # Configuração do Tailwind CSS
├── postcss.config.js                # PostCSS (Tailwind + Autoprefixer)
└── src/
    ├── main.jsx                     # Bootstrap React — importa leaflet.css e index.css
    ├── index.css                    # Tailwind directives + estilos globais + scrollbar
    ├── App.jsx                      # Layout raiz: sidebar + painel de formulário + mapa + painel de análise
    └── components/
        ├── Sidebar.jsx              # Sidebar escura com logo e navegação
        ├── RouteForm.jsx            # Formulário com todos os parâmetros do RotasRequest (com tooltips explicativos)
        ├── MapView.jsx              # Mapa Leaflet com marcadores numerados e polilinha da rota
        ├── AnalysisPanel.jsx        # Painel de resultado: cards-resumo, gráfico de evolução (Chart.js) e lista de cidades
        └── MedicalIllustration.jsx  # SVG ilustrativo exibido antes de gerar a rota
```

### Stack do frontend

| Camada | Tecnologia |
|---|---|
| Framework | React 18 + Vite 5 |
| Estilo | Tailwind CSS 3 |
| Mapa | Leaflet.js (vanilla, sem react-leaflet) |
| Gráficos | Chart.js (gráfico de evolução da distância por época) |
| HTTP | `fetch` nativo com proxy Vite |
| Ícones | SVGs inline |

### Fluxo do frontend

```
Usuário preenche RouteForm (mensagem até 500 chars + parâmetros do AG)
    │  POST /rotas/ (proxy Vite → localhost:8000)
    ▼
App.jsx recebe GeoJSON FeatureCollection + metadados de execução
    │  passa geoJson para MapView e AnalysisPanel
    ▼
MapView renderiza:
    - Marcadores numerados (vermelho = prioridade 1, azul = prioridade 2)
    - Polilinha tracejada conectando as cidades na ordem de visita
    - Popup por cidade: nome, UF, produto, prioridade
    - Legenda no canto inferior esquerdo

AnalysisPanel renderiza:
    - Cards-resumo: total de cidades, distância (km), aptidão final
    - Gráfico de evolução da distância por época (historico_evolucao)
    - Aviso de parada antecipada, se `parou_antecipadamente=true`
    - Lista ordenada das cidades da rota com produto/prioridade
```

Validações client-side em `RouteForm.jsx`: mensagem entre 20–500 caracteres (contador + erro inline), e o toggle "Parada Antecipada" só fica habilitado quando o Elitismo está ativo (desabilitado com tooltip explicando o motivo).

---

## Endpoints

### `POST /rotas/`
Único ponto de entrada funcional da API (além de `/health`). Recebe a descrição textual da rota e os parâmetros do AG.

**Request body (`RotasRequest`):**

| Campo | Tipo | Restrições | Descrição |
|---|---|---|---|
| `mensagem` | str | 20–500 chars | Descrição em linguagem natural da rota e produtos |
| `epocas` | int | 1–100.000 | Número de gerações do AG |
| `elitismo` | int | 0 ou 1 | 1 = preserva os verdadeiros melhores indivíduos a cada geração (independente do método de seleção dos pais) |
| `grau_mutacao` | float | 0.0–10.0 | Taxa de mutação em % (dividida por 100 internamente) |
| `populacao_apenas_aleatoria` | int | 0 ou 1 | Reservado para extensões futuras (não altera o comportamento atual) |
| `tamanho_populacao` | int | 1–10.000 | Número de indivíduos na população |
| `tamanho_elite` | int | ≥ 1, < `tamanho_populacao` | Indivíduos usados como pais (e preservados, se elitismo=1) |
| `tipo_selecao` | "truncamento" \| "torneio" | padrão "truncamento" | Método de seleção dos pais |
| `tipo_crossover` | "ox" \| "erx" | padrão "ox" | Operador de crossover |
| `tipo_mutacao` | "swap" \| "inversao" \| "ambos" \| "or_opt" | padrão "ambos" | Operador de mutação |
| `usar_2opt` | int | 0 ou 1 | 1 = aplica busca local 2-opt em cada filho gerado |
| `tipo_inicializacao` | "aleatoria" \| "vizinho_mais_proximo" | padrão "aleatoria" | Estratégia de geração da população inicial |
| `usar_parada_antecipada` | int | 0 ou 1 | 1 = encerra o AG se a aptidão não melhorar por `paciencia_parada_antecipada` épocas. **Só tem efeito com `elitismo=1`** |
| `paciencia_parada_antecipada` | int | ≥ 1, padrão 30 | Épocas consecutivas sem melhora toleradas antes de parar |

**Resposta:**

```json
{
  "type": "FeatureCollection",
  "features": [ /* uma Feature Point por cidade, na ordem de visita */ ],
  "km_total": 0.0,
  "aptidao_final": 0.0,
  "total_cidades": 0,
  "historico_evolucao": [ {"epoca": 0, "distancia_km": 0.0, "aptidao": 0.0} ],
  "epocas_executadas": 0,
  "parou_antecipadamente": false
}
```

Cada `Feature` traz em `properties`: `ordem_visita`, `cidade`, `uf`, `regiao_tradicional`, `produto`, `prioridade`.

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
    │  Trata blocos "região/cidade + produto" isoladamente quando há múltiplos na mensagem
    │  Cidades fronteiriças/vizinhas: NÃO usa as ferramentas locais (não há dado de adjacência) —
    │  usa o conhecimento geográfico do próprio modelo, de forma conservadora
    │  Retorna: list[{"cod_ibge": int, "produto_id": int}], com a cidade de partida reordenada
    │  para o índice 0 quando identificada na mensagem (_reordenar_partida)
    │
    ▼
CidadeService.montar_cidades_com_produtos(pares)
    │  Retorna: list[Cidade] com produto preenchido
    │
    ▼
Inicialização da população (tipo_inicializacao):
    │  'aleatoria' → ag.gerar_populacao_aleatoria(...)
    │  'vizinho_mais_proximo' → inclui ag.gerar_individuo_vizinho_mais_proximo(...) na população inicial
    │  Tamanho é ajustado automaticamente para min(tamanho_populacao, (N-1)!)
    │
    ▼
Loop por até `epocas` gerações (pode parar antes — ver parada antecipada):
    │  Seleção dos pais (tipo_selecao): seleciona_melhores_individuos (truncamento) OU selecionar_por_torneio
    │  Elitismo (se ativo): SEMPRE recalcula os verdadeiros melhores via seleciona_melhores_individuos,
    │      independente do método de seleção dos pais (torneio é estocástico e pode não sortear o melhor)
    │  Crossover (tipo_crossover): cruzamento_ox OU cruzamento_erx
    │  Mutação (tipo_mutacao): mutacao_simples, mutacao_inversao, ambos, ou mutacao_or_opt
    │  Busca local 2-opt (usar_2opt=1, opcional): busca_local_2opt em cada filho
    │  Parada antecipada (usar_parada_antecipada=1 e elitismo=1): encerra se não houver
    │      melhora por `paciencia_parada_antecipada` épocas seguidas
    │
    ▼
melhor Individuo → GeoJSON FeatureCollection + historico_evolucao + epocas_executadas + parou_antecipadamente
```

---

## Classes de Domínio (`models/`)

### `Cidade`
- Identificador canônico: `cod_ibge: int`
- `regiao_tradicional: str | None` — campo do CSV do IBGE para filtro regional
- `produto: Produto | None` — a cidade de partida tem `produto=None`
- `distancia_para(outra)` — fórmula de Haversine; **nunca modificar**
- `RAIO_TERRA_KM = 6371.0` — constante de classe
- `__eq__` e `__hash__` baseados em `cod_ibge` (usados por `in`/`.remove()` sobre listas de cidades — mantenha o par ao editar)

### `Individuo`
- `cromossomo: list[Cidade]` — sempre `[partida, c1, c2, ..., partida]` (rota circular)
- `calcular_aptidao()` — define `self.distancia` e `self.aptidao` como efeito colateral; acesse-os **somente após** chamar esse método
- `aptidao = distancia_total - bonificacao_prioridade()` — **menor aptidão ainda é melhor** (convenção de custo/minimização, não a "fitness" darwinista clássica — mantenha consistente em toda comparação/seleção)
- `_BONIFICACAO_POR_ANTECIPACAO = 100.0` — bônus subtraído da aptidão por cidade de prioridade 1 ("vacina"), ponderado pela posição na rota (quanto mais cedo, maior o bônus); ordem de grandeza pensada para orientar a seleção sem sobrepor economias reais de distância
- Toda nova regra de priorização de rota segue o padrão: adicionar método `_bonificacao_X()` (ou `_penalidade_X()`, se for o caso) e compor em `calcular_aptidao()`
- `is_valido()` — verifica integridade do cromossomo (hoje só é usada pela suíte de testes, não em runtime)
- `rota_nomes()` — retorna lista de nomes na ordem de visita (usado no log final de `RotaService`)
- `copiar()` — cópia independente do indivíduo (usada pelos operadores em `algoritmos_geneticos.py`)
- **Sem lógica genética nesta classe**

### `Produto`
- `prioridade: int` — `1` = alta urgência (vacinas/medicamentos), `2` = baixa urgência (insumos)
- Validação no `__init__`: `prioridade not in {1, 2}` lança `ValueError`

---

## Services

### `CidadeService` (`cidade_service` — singleton)
- Carrega `data/cidades.csv` uma única vez na inicialização
- Coordenadas armazenadas como inteiros no CSV (ex.: `-119283`); convertidas para graus decimais via `_parse_coordenada()` com inferência automática do divisor
- `pesquisar_por_nome(termo)` — substring unidirecional (`termo in nome`); cuidado com sufixos de UF (ex.: "Niterói-RJ") — `LLMService` já normaliza isso antes de chamar
- `listar_por_uf`, `listar_por_regiao_tradicional`, `buscar_por_cod_ibge` — usados pelo `LLMService` como ferramentas de function calling
- `montar_cidades_com_produtos(pares)` — recebe lista de `{cod_ibge, produto_id}` e retorna novas instâncias de `Cidade` com produto atribuído; pares inválidos são silenciosamente ignorados

### `ProdutoService` (`produto_service` — singleton)
- Carrega `data/produtos.csv` uma única vez
- `pesquisar_por_nome(termo)` — busca em duas camadas: (1) substring bidirecional exata; (2) prefixo por palavras, exigindo que **todas** as palavras significativas do termo (>2 chars) correspondam a alguma palavra do nome — evita que uma palavra genérica em comum (ex.: "vacina") faça termos mais específicos ("vacina covid") casarem com produtos não relacionados ("Vacina da Gripe")

### `LLMService`
- Usa a API OpenAI com **function calling** para interpretar a mensagem em linguagem natural
- Loop de tool calling até o modelo emitir resposta final (`finish_reason != "tool_calls"`)
- Ferramentas disponíveis: `pesquisar_cidade_por_nome`, `listar_cidades_por_regiao`, `listar_cidades_por_uf`, `pesquisar_produto_por_nome`, `buscar_cidade_por_cod_ibge`
- `_SYSTEM_PROMPT` cobre explicitamente: identificação de cidade de partida (`_reordenar_partida` + regex de fallback), mensagens com múltiplos blocos região/cidade+produto (tratados isoladamente, sem misturar produtos entre blocos), e cidades fronteiriças/vizinhas (resolvidas pelo conhecimento geográfico do próprio modelo, de forma conservadora, sem usar as ferramentas locais — não há dado de adjacência no CSV)
- Retorna lista de `{"cod_ibge": int, "produto_id": int}`

### `RotaService`
- Orquestra: LLMService → CidadeService → AG → GeoJSON
- `grau_mutacao` recebido em % (0–10), convertido para probabilidade (0.0–1.0) antes de chamar os operadores
- Elitismo: quando `elitismo=1`, sempre recalcula a elite real via `seleciona_melhores_individuos`, independente de `tipo_selecao` (evita que o torneio, estocástico, perca o melhor indivíduo entre gerações)
- Parada antecipada: só ativa quando `elitismo=1` (aptidão não-crescente garantida); rastreia a melhor aptidão a cada época e encerra o loop via `break` ao atingir `paciencia_parada_antecipada` sem melhora
- Imprime progresso a cada 10% das épocas no stdout (`historico_evolucao`), mais o log de parada antecipada quando aplicável
- Retorna também `epocas_executadas` e `parou_antecipadamente` no payload de resposta

### `services/algoritmos_geneticos.py`
- **Inicialização**: `gerar_individuo_aleatorio(partida, cidades)`; `gerar_populacao_aleatoria(quantidade, partida, cidades, melhores_individuos=None)` (ajusta `quantidade` para `min(quantidade, (N-1)!)`); `gerar_individuo_vizinho_mais_proximo(partida, cidades)` — heurística gulosa
- **Seleção**: `seleciona_melhores_individuos(populacao, quantidade)` (truncamento, ordena por `calcular_aptidao()` ascendente); `selecionar_por_torneio(populacao, quantidade, tamanho_torneio=3)` (estocástico)
- **Crossover**: `cruzamento_ox(parent1, parent2, partida)` (Order Crossover); `cruzamento_erx(parent1, parent2, partida)` (Edge Recombination — preserva arestas, melhor para TSP puro)
- **Mutação**: `mutacao_simples` (swap adjacente), `mutacao_inversao` (inverte segmento), `mutacao_or_opt` (realoca segmento de 1–3 cidades)
- **Busca local**: `busca_local_2opt(individuo, max_passagens=1)` — O(n²) por passagem; para poucas cidades pode convergir ao ótimo em poucas épocas, então reduza `tamanho_populacao`/`epocas` ao ativar

---

## Invariantes Críticos

1. `cromossomo[0] == cromossomo[-1] == partida` — sempre, sem exceção
2. `cromossomo[1:-1]` não contém duplicatas nem a cidade de partida
3. `calcular_aptidao()` deve ser chamado antes de acessar `individuo.distancia` ou `individuo.aptidao`
4. `cromossomo` é sempre `list[Cidade]`, nunca string ou tuple
5. Lógica genética pertence a `services/algoritmos_geneticos.py`, não a `Individuo`
6. O `.env` **nunca deve ser commitado** — use `.env.example` como referência
7. Aptidão usa convenção de **minimização** (menor = melhor) em toda a base — nunca inverter o sinal isoladamente em um único operador
8. Elitismo (`elitismo=1`) deve sempre preservar os verdadeiros melhores indivíduos da população, nunca apenas a saída do método de seleção de pais (torneio ≠ elite)

---

## Convenções de Código

- Docstrings estilo NumPy (`Parâmetros / Retorna / Notas`)
- Type hints em todos os métodos
- Listas no plural: `populacao`, `cidades`, `melhores`
- Métodos privados de ajuste de aptidão: prefixo `_penalidade_` ou `_bonificacao_` conforme o efeito (ex.: `_bonificacao_prioridade()`)
- Proibido abreviar: `calcular_aptidao()` não `calc_apt()`
- Singletons dos services importados diretamente: `from services.cidade_service import cidade_service`
- Toda mudança em `services/algoritmos_geneticos.py` ou `rota_service.py` deve manter (e, se possível, ganhar cobertura em) `tests/test_algoritmos_geneticos.py`
