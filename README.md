# Sistema de Otimizacao de Rotas Medicas

Projeto da Fase 2 da pos-graduacao FIAP - IA para Devs. A aplicacao otimiza rotas de entrega de medicamentos, vacinas e insumos medicos usando Algoritmos Geneticos para uma variacao do Problema do Caixeiro Viajante (TSP).

## Integrantes

- Gustavo Denobi
- Gilberto Cunha
- Thiago Garbulha
- Vitor Arruda

## Visao Geral

O sistema possui duas partes:

- `api-rotas-medicas/`: API FastAPI responsavel por autenticacao, interpretacao da mensagem, execucao do algoritmo genetico e retorno da rota em GeoJSON.
- `frontend-rotas-medicas/`: frontend React + Vite responsavel por login, formulario de parametros, mapa Leaflet e painel de analise.

Fluxo principal:

1. O usuario faz login.
2. O usuario descreve uma rota em linguagem natural.
3. A API interpreta a mensagem via LLM ou mock local.
4. A API monta as cidades/produtos usando os CSVs locais.
5. O algoritmo genetico otimiza a rota.
6. O frontend exibe a rota no mapa e os graficos de evolucao.

## Requisitos

- Python 3.11+
- Node.js 18+
- npm

## Backend

Entre na pasta da API:

```bash
cd api-rotas-medicas
```

Crie e ative um ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instale as dependencias:

```bash
pip install -r requirements.txt
```

Crie o arquivo `.env` com base no exemplo:

```bash
cp .env.example .env
```

Exemplo de `.env`:

```env
OPENAI_API_KEY=sua-chave-openai
MODELO_CHAT=gpt-4.1-mini
LLM_MOCK=0
AUTH_USUARIO=admin
AUTH_SENHA=admin
```

Para testar sem cota da OpenAI, use o mock local:

```env
LLM_MOCK=1
```

Com `LLM_MOCK=1`, a API nao chama a OpenAI. Ela tenta inferir cidades/produtos pela mensagem usando os CSVs locais e, se nao conseguir, usa uma lista padrao em `api-rotas-medicas/services/llm_service.py`.

Para testar a restricao de capacidade no modo mock, preencha o campo "Capacidade do Veiculo (kg)" no frontend ou envie `capacidade_veiculo_kg` no payload da API. O mock altera apenas a interpretacao de cidades/produtos; os parametros do algoritmo continuam vindo da requisicao.

Suba a API:

```bash
uvicorn main:app --reload
```

URL padrao:

```text
http://localhost:8000
```

Health check:

```bash
curl http://localhost:8000/health
```

## Frontend

Em outro terminal, entre na pasta do frontend:

```bash
cd frontend-rotas-medicas
```

Instale as dependencias:

```bash
npm install
```

Suba o frontend:

```bash
npm run dev
```

URL padrao:

```text
http://localhost:5173
```

O Vite possui proxy para a API em `localhost:8000`.

## Autenticacao

A aplicacao usa autenticacao simples com usuario e senha definidos no `.env`:

```env
AUTH_USUARIO=admin
AUTH_SENHA=admin
```

Endpoints:

- `POST /auth/login`: autentica e retorna um token.
- `POST /auth/logout`: revoga o token atual.
- `POST /rotas/`: endpoint protegido que calcula a rota otimizada.
- `GET /health`: verifica se a API esta no ar.

## Endpoint Principal

`POST /rotas/`

Recebe a mensagem da rota e parametros do algoritmo genetico, como:

- `epocas`
- `tamanho_populacao`
- `tamanho_elite`
- `grau_mutacao`
- `capacidade_veiculo_kg`: capacidade maxima opcional do veiculo em kg
- `elitismo`
- `tipo_selecao`: `truncamento` ou `torneio`
- `tipo_crossover`: `ox` ou `erx`
- `tipo_mutacao`: `swap`, `inversao`, `ambos` ou `or_opt`
- `usar_2opt`
- `tipo_inicializacao`: `aleatoria` ou `vizinho_mais_proximo`
- `usar_parada_antecipada`

A resposta e um `FeatureCollection` GeoJSON com a rota, distancia total, historico de evolucao, metricas de aptidao, diagnostico de prioridade e diagnostico de capacidade de carga.

Exemplo minimo de payload com capacidade:

```json
{
  "mensagem": "Monte uma rota para entregar vacinas e medicamentos em Sao Paulo, Campinas e Santos.",
  "epocas": 100,
  "elitismo": 1,
  "grau_mutacao": 2,
  "populacao_apenas_aleatoria": 1,
  "tamanho_populacao": 100,
  "tamanho_elite": 10,
  "capacidade_veiculo_kg": 10
}
```

## Algoritmo Genetico

O algoritmo representa cada solucao como uma rota circular:

```text
cidade_partida -> cidade_1 -> cidade_2 -> ... -> cidade_partida
```

Principais caracteristicas:

- Populacao inicial aleatoria ou por vizinho mais proximo.
- Selecao por truncamento ou torneio.
- Crossover OX ou ERX.
- Mutacao por swap, inversao, ambos ou Or-opt.
- Busca local 2-opt opcional.
- Elitismo opcional.
- Parada antecipada opcional.
- Fitness baseado em distancia total, bonificacao para entregas de prioridade 1 e penalidade quando a carga total excede `capacidade_veiculo_kg`.

## Dados

Os dados locais ficam em:

- `api-rotas-medicas/data/cidades.csv`
- `api-rotas-medicas/data/produtos.csv`

O arquivo de produtos possui a coluna `PESO_KG`, usada para calcular a carga total da rota. Quando o usuario informa a capacidade do veiculo no frontend, a API retorna:

- `carga_total_kg`
- `capacidade_veiculo_kg`
- `excesso_carga_kg`
- `capacidade_excedida`
- `uso_capacidade_percentual`

## Testes

Rode os testes do backend:

```bash
cd api-rotas-medicas
source .venv/bin/activate
pytest tests/ -q
```

## Build do Frontend

```bash
cd frontend-rotas-medicas
npm run build
```
