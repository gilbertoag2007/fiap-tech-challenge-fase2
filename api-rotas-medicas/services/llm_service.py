import json
import re
import unicodedata
from typing import Any
from openai import OpenAI
from config.settings import Settings
from services.cidade_service import cidade_service
from services.produto_service import produto_service

class LLMService:

    _settings = Settings()
    _client: OpenAI | None = None
    _PARES_MOCK_PADRAO: list[dict[str, int]] = [
        {"cod_ibge": 3550308, "produto_id": 1},   # São Paulo -> Vacina da Covid
        {"cod_ibge": 3509502, "produto_id": 2},   # Campinas -> Seringa
        {"cod_ibge": 3548500, "produto_id": 3},   # Santos -> Vacina da Gripe
        {"cod_ibge": 3304557, "produto_id": 4},   # Rio de Janeiro -> Gase
        {"cod_ibge": 3303302, "produto_id": 5},   # Niterói -> Algodão
        {"cod_ibge": 3301702, "produto_id": 6},   # Duque de Caxias -> Vacina BCG
        {"cod_ibge": 3106200, "produto_id": 7},   # Belo Horizonte -> Outras vacinas
        {"cod_ibge": 4106902, "produto_id": 8},   # Curitiba -> Outros insumos
        {"cod_ibge": 4314902, "produto_id": 9},   # Porto Alegre -> Remédio de Hipertensão
        {"cod_ibge": 5002704, "produto_id": 10},  # Campo Grande -> Remédio antialergíco
        {"cod_ibge": 5103403, "produto_id": 11},  # Cuiabá -> Outros medicamentos
        {"cod_ibge": 5208707, "produto_id": 1},   # Goiânia -> Vacina da Covid
        {"cod_ibge": 3205309, "produto_id": 2},   # Vitória -> Seringa
        {"cod_ibge": 4205407, "produto_id": 3},   # Florianópolis -> Vacina da Gripe
        {"cod_ibge": 1721000, "produto_id": 4},   # Palmas -> Gase
        {"cod_ibge": 1501402, "produto_id": 5},   # Belém -> Algodão
        {"cod_ibge": 1302603, "produto_id": 6},   # Manaus -> Vacina BCG
        {"cod_ibge": 2927408, "produto_id": 7},   # Salvador -> Outras vacinas
        {"cod_ibge": 2611606, "produto_id": 8},   # Recife -> Outros insumos
        {"cod_ibge": 2507507, "produto_id": 9},   # João Pessoa -> Remédio de Hipertensão
        {"cod_ibge": 2704302, "produto_id": 10},  # Maceió -> Remédio antialergíco
        {"cod_ibge": 2408102, "produto_id": 11},  # Natal -> Outros medicamentos
        {"cod_ibge": 2800308, "produto_id": 1},   # Aracaju -> Vacina da Covid
        {"cod_ibge": 2211001, "produto_id": 2},   # Teresina -> Seringa
        {"cod_ibge": 2111300, "produto_id": 3},   # São Luís -> Vacina da Gripe
        {"cod_ibge": 1100205, "produto_id": 4},   # Porto Velho -> Gase
        {"cod_ibge": 1200401, "produto_id": 5},   # Rio Branco -> Algodão
    ]

    @classmethod
    def _get_client(cls) -> OpenAI:
        if cls._client is None:
            cls._client = OpenAI(api_key=cls._settings.OPENAI_API_KEY)
        return cls._client

    # ---------------------------------------------------------------------------
    # Contexto fixo enviado ao ChatGPT em todas as chamadas
    # ---------------------------------------------------------------------------

    _SYSTEM_PROMPT = """Você é um assistente especializado em logística de saúde pública no Brasil.

    Sua tarefa é interpretar uma mensagem em linguagem natural que descreve uma rota de entrega
    de medicamentos e insumos, e identificar:
    1. Quais municípios brasileiros devem receber entrega.
    2. Qual produto deve ser entregue em cada município.

    Para identificar os municípios, utilize as funções de pesquisa disponíveis — prefira sempre
    a pesquisa local. Siga esta ordem de preferência:
    - Quando a mensagem citar uma região (ex.: "região metropolitana do Rio de Janeiro"), use
        a função listar_cidades_por_regiao.
    - Quando a mensagem citar um estado inteiro, use listar_cidades_por_uf.
    - Quando citar nomes específicos de municípios, use pesquisar_cidade_por_nome para cada um.
    - Para confirmar ou validar o código IBGE de um município já identificado, use
        buscar_cidade_por_cod_ibge.
    - Caso não encontre o código IBGE pelas funções locais, utilize seu conhecimento para inferir.

    CIDADES FRONTEIRIÇAS/VIZINHAS (adjacência geográfica):
    - Quando a mensagem pedir municípios que fazem fronteira ou são vizinhos de uma cidade
      (ex.: "cidades que fazem fronteira com a cidade do Rio de Janeiro"), NÃO utilize as
      ferramentas de pesquisa (pesquisar_cidade_por_nome, listar_cidades_por_regiao,
      listar_cidades_por_uf) para descobrir quais são essas cidades — os dados locais não
      contêm nenhuma relação de adjacência/fronteira entre municípios.
    - Em vez disso, identifique diretamente, usando seu próprio conhecimento geográfico do
      Brasil, o nome e o código IBGE de cada município fronteiriço, e inclua cada par
      (cod_ibge, produto_id) diretamente na resposta final.
    - Seja rigoroso e conservador: inclua APENAS municípios cuja fronteira direta com a
      cidade de referência você tem certeza — nunca inclua um município só por pertencer à
      mesma região tradicional, à mesma região metropolitana ou por estar "próximo"/na
      mesma área geral. Proximidade ou vizinhança de região NÃO é fronteira direta.
    - Na dúvida sobre se dois municípios realmente compartilham fronteira, prefira omitir o
      município a incluí-lo incorretamente.

    Para identificar os produtos, utilize a função pesquisar_produto_por_nome para cada produto
    mencionado na mensagem. Se a busca retornar lista vazia, tente novamente com um termo mais
    curto ou com apenas a palavra principal do produto (ex.: se "vacinas da Covid 19" não
    retornar resultado, tente "vacina covid" ou somente "covid").

    MENSAGENS COM MÚLTIPLOS BLOCOS REGIÃO/CIDADE + PRODUTO:
    - Uma mensagem pode descrever mais de um trecho independente, cada um combinando um produto
      com um conjunto de cidades (ex.: "entregar vacinas na região X e seringas na região Y").
      Trate cada trecho como um bloco isolado: NUNCA associe um produto às cidades de um bloco
      diferente daquele em que ele foi mencionado.
    - Se apenas um dos blocos mencionar explicitamente a UF (ex.: "região Y do estado do Rio de
      Janeiro"), aplique essa mesma UF aos demais blocos da mensagem que não tiverem UF
      explícita, desde que nenhum outro estado tenha sido citado.
    - Resolva cada bloco por completo (cidades do bloco + produto do bloco) antes de passar para
      o próximo, e só monte a lista final de pares depois de ter todos os blocos resolvidos —
      para não perder nem misturar itens entre eles.

    IDENTIFICAÇÃO DA CIDADE DE PARTIDA:
    - Analise a mensagem para identificar se há uma cidade de partida/origem explicitamente
      citada (expressões como "saindo de", "partindo de", "a partir de", "origem em",
      "hub em", "base em", "depot em", "ponto de partida", "cidade de partida é",
      "cidade de partida:").
    - Se uma cidade de partida for identificada, ela DEVE ser o PRIMEIRO elemento da lista JSON.
      Se essa cidade não receber nenhum produto específico, associe a ela o mesmo produto_id
      do produto principal mencionado na mensagem.
    - Se nenhuma cidade de partida for explicitamente mencionada, não altere a ordem dos pares.

    Ao finalizar todas as pesquisas, responda EXCLUSIVAMENTE com um JSON puro, sem texto adicional
    e sem markdown, no seguinte formato:
    [{"cod_ibge": 3301702, "produto_id": 1}, {"cod_ibge": 3303302, "produto_id": 2}]

    Regras:
    - Inclua apenas pares onde AMBOS os valores (cod_ibge e produto_id) foram encontrados.
    - Se um município recebe mais de um produto, inclua um par para cada produto.
    - Se nenhum par válido for encontrado, retorne uma lista vazia: []
    - Não inclua explicações, comentários ou blocos de código — apenas o JSON."""

# ---------------------------------------------------------------------------
# Definição das ferramentas (function calling)
# ---------------------------------------------------------------------------

    _TOOLS: list[dict[str, Any]] = [
        {
            "type": "function",
            "function": {
                "name": "pesquisar_cidade_por_nome",
                "description": (
                    "Pesquisa municípios brasileiros pelo nome ou fragmento do nome "
                    "no banco de dados local do IBGE."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "termo": {
                            "type": "string",
                            "description": "Nome ou parte do nome da cidade (ex.: 'Duque de Caxias', 'Teresópolis').",
                        }
                    },
                    "required": ["termo"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "listar_cidades_por_regiao",
                "description": (
                    "Lista todos os municípios pertencentes a uma região tradicional e UF"
                    "(ex.: 'Região Metropolitana do Rio de Janeiro', 'Vale do Paraíba')."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "regiao": {
                            "type": "string",
                            "description": "Nome da região tradicional conforme cadastrado no banco de dados local.",
                        },
                        "uf": {
                            "type": "string",
                            "description": "Sigla do estado com 2 letras maiúsculas (ex.: 'SP', 'RJ', 'MG').",
                        }
                    },
                    "required": ["regiao", "uf"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "listar_cidades_por_uf",
                "description": "Lista todos os municípios de um estado brasileiro pela sigla UF.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "uf": {
                            "type": "string",
                            "description": "Sigla do estado com 2 letras maiúsculas (ex.: 'SP', 'RJ', 'MG').",
                        }
                    },
                    "required": ["uf"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "pesquisar_produto_por_nome",
                "description": (
                    "Pesquisa produtos de saúde (vacinas, medicamentos, insumos) "
                    "pelo nome no banco de dados local."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "termo": {
                            "type": "string",
                            "description": "Nome ou fragmento do nome do produto (ex.: 'vacina covid', 'seringa', 'insulina').",
                        }
                    },
                    "required": ["termo"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "buscar_cidade_por_cod_ibge",
                "description": (
                    "Busca um município brasileiro pelo código IBGE no banco de dados local. "
                    "Use para confirmar ou validar o código IBGE de uma cidade já identificada."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cod_ibge": {
                            "type": "integer",
                            "description": "Código IBGE do município (ex.: 3304557 para Rio de Janeiro).",
                        }
                    },
                    "required": ["cod_ibge"],
                },
            },
        },
    ]


    # ---------------------------------------------------------------------------
    # Reordenação da cidade de partida
    # ---------------------------------------------------------------------------

    _PADROES_PARTIDA: list[str] = [
        r"cidade de partida[^é\w]*(?:é\s+)?(.+?)(?:\.|,|$)",
        r"ponto de partida[^é\w]*(?:é\s+)?(.+?)(?:\.|,|$)",
        r"saindo de\s+(.+?)(?:\.|,|$)",
        r"partindo de\s+(.+?)(?:\.|,|$)",
        r"a partir de\s+(.+?)(?:\.|,|$)",
        r"origem em\s+(.+?)(?:\.|,|$)",
        r"hub em\s+(.+?)(?:\.|,|$)",
        r"base em\s+(.+?)(?:\.|,|$)",
        r"depot em\s+(.+?)(?:\.|,|$)",
    ]

    def _reordenar_partida(
        self, pares: list[dict[str, int]], mensagem: str
    ) -> list[dict[str, int]]:
        """
        Garante que a cidade de partida mencionada na mensagem seja o primeiro elemento.

        Extrai o nome da cidade via expressões regulares, localiza seu cod_ibge no banco
        local e move o par correspondente para o índice 0. Se o par não estiver na lista
        (a LLM pode não tê-lo incluído), insere um com o produto_id do primeiro par.

        Parâmetros
        ----------
        pares : list[dict[str, int]] — lista de pares retornada pela LLM.
        mensagem : str — mensagem original do usuário.

        Retorna
        -------
        list[dict[str, int]] — lista reordenada (ou original se partida não identificada).
        """
        for padrao in self._PADROES_PARTIDA:
            match = re.search(padrao, mensagem, re.IGNORECASE)
            if not match:
                continue

            nome_cidade = match.group(1).strip().rstrip(".")
            # Remove sufixo de UF (ex.: "Niterói-RJ" → "Niterói") pois o nome
            # cadastrado no CSV do IBGE não inclui a sigla do estado.
            nome_cidade = re.sub(r"\s*-\s*[A-Za-z]{2}$", "", nome_cidade).strip()
            cidades = cidade_service.pesquisar_por_nome(nome_cidade)
            if not cidades:
                continue

            cod_ibge_partida = cidades[0].cod_ibge
            idx = next(
                (i for i, p in enumerate(pares) if p.get("cod_ibge") == cod_ibge_partida),
                None,
            )

            if idx is None:
                produto_id_principal = pares[0]["produto_id"] if pares else 1
                pares.insert(0, {"cod_ibge": cod_ibge_partida, "produto_id": produto_id_principal})
                print(f"[LLMService] Cidade de partida '{cidades[0].nome}' inserida na posição 0.")
            elif idx != 0:
                pares.insert(0, pares.pop(idx))
                print(f"[LLMService] Cidade de partida '{cidades[0].nome}' movida para posição 0.")

            return pares

        return pares

    # ---------------------------------------------------------------------------
    # Execução local das ferramentas
    # ---------------------------------------------------------------------------

    @staticmethod
    def _executar_ferramenta(nome: str, args: dict[str, str]) -> list[dict[str, Any]]:
        """Despacha a chamada de ferramenta do ChatGPT para o service local correto."""
        if nome == "pesquisar_cidade_por_nome":
            return [
                {"cod_ibge": c.cod_ibge, "nome": c.nome, "uf": c.uf}
                for c in cidade_service.pesquisar_por_nome(args["termo"])
            ]
        if nome == "listar_cidades_por_regiao":
            return [
                {"cod_ibge": c.cod_ibge, "nome": c.nome, "uf": c.uf}
                for c in cidade_service.listar_por_regiao_tradicional(args["regiao"], uf=args["uf"])
            ]
        if nome == "listar_cidades_por_uf":
            return [
                {"cod_ibge": c.cod_ibge, "nome": c.nome, "uf": c.uf}
                for c in cidade_service.listar_por_uf(args["uf"])
            ]
        if nome == "pesquisar_produto_por_nome":
            return [
                {"id": p.id, "nome": p.nome, "prioridade": p.prioridade}
                for p in produto_service.pesquisar_por_nome(args["termo"])
            ]
        if nome == "buscar_cidade_por_cod_ibge":
            cidade = cidade_service.buscar_por_cod_ibge(int(args["cod_ibge"]))
            if cidade is None:
                return []
            return [{"cod_ibge": cidade.cod_ibge, "nome": cidade.nome, "uf": cidade.uf}]
        return []

    # ---------------------------------------------------------------------------
    # Mock local para testes sem cota da OpenAI
    # ---------------------------------------------------------------------------

    @staticmethod
    def _normalizar_texto(texto: str) -> str:
        texto_ascii = unicodedata.normalize("NFKD", texto)
        texto_ascii = "".join(c for c in texto_ascii if not unicodedata.combining(c))
        return texto_ascii.casefold()

    @staticmethod
    def _encontrar_termo(texto_normalizado: str, termo_normalizado: str) -> int:
        match = re.search(rf"(?<!\w){re.escape(termo_normalizado)}(?!\w)", texto_normalizado)
        return match.start() if match else -1

    def _encontrar_produto_mock(self, mensagem_normalizada: str, nome_produto: str) -> int:
        nome_normalizado = self._normalizar_texto(nome_produto)
        posicao = self._encontrar_termo(mensagem_normalizada, nome_normalizado)
        if posicao >= 0:
            return posicao

        palavras_produto = [p for p in re.findall(r"\w+", nome_normalizado) if len(p) > 3]
        palavras_mensagem = [
            (match.start(), match.group(0))
            for match in re.finditer(r"\w+", mensagem_normalizada)
            if len(match.group(0)) > 3
        ]
        for posicao_palavra, palavra_mensagem in palavras_mensagem:
            if any(
                palavra_mensagem.startswith(palavra_produto)
                or palavra_produto.startswith(palavra_mensagem)
                for palavra_produto in palavras_produto
            ):
                return posicao_palavra

        return -1

    def _pares_mock_padrao(self) -> list[dict[str, int]]:
        pares: list[dict[str, int]] = []

        for par in self._PARES_MOCK_PADRAO:
            cod_ibge = par["cod_ibge"]
            produto_id = par["produto_id"]
            if cidade_service.buscar_por_cod_ibge(cod_ibge) is None:
                continue
            if produto_service.buscar_por_id(produto_id) is None:
                continue
            pares.append({"cod_ibge": cod_ibge, "produto_id": produto_id})

        return pares

    def _interpretar_mensagem_mock(self, mensagem: str) -> list[dict[str, int]]:
        """
        Interpreta a mensagem sem chamar a OpenAI, usando apenas os CSVs locais.

        O mock procura nomes de cidades e produtos literalmente mencionados no
        texto. Se encontrar cidades, associa cada uma ao produto mais próximo:
        primeiro produto citado antes da cidade; se não houver, o primeiro produto
        citado na mensagem. Se não encontrar cidades ou produtos suficientes,
        retorna uma rota padrão pequena para manter o frontend testável.
        """
        mensagem_normalizada = self._normalizar_texto(mensagem)
        cidades = getattr(cidade_service, "_cidades", [])
        produtos = getattr(produto_service, "_produtos", [])

        cidades_mencionadas = [
            (self._encontrar_termo(mensagem_normalizada, self._normalizar_texto(cidade.nome)), cidade)
            for cidade in cidades
        ]
        produtos_mencionados = [
            (self._encontrar_produto_mock(mensagem_normalizada, produto.nome), produto)
            for produto in produtos
        ]

        cidades_mencionadas = sorted(
            [(pos, cidade) for pos, cidade in cidades_mencionadas if pos >= 0],
            key=lambda item: item[0],
        )
        produtos_mencionados = sorted(
            [(pos, produto) for pos, produto in produtos_mencionados if pos >= 0],
            key=lambda item: (item[0], item[1].id),
        )

        if not cidades_mencionadas:
            pares = self._pares_mock_padrao()
            print(f"[LLMService] Mock ativo: nenhuma cidade inferida; usando {len(pares)} pares padrão do CSV.")
            return self._reordenar_partida(pares, mensagem)

        if not produtos_mencionados:
            produto_padrao = produto_service.pesquisar_por_nome("vacina")
            produto_id = produto_padrao[0].id if produto_padrao else 1
            produtos_mencionados = [(0, produto_service.buscar_por_id(produto_id))]

        pares: list[dict[str, int]] = []
        produto_principal = next((produto for _, produto in produtos_mencionados if produto is not None), None)
        for pos_cidade, cidade in cidades_mencionadas:
            produtos_anteriores = [
                (pos_produto, produto)
                for pos_produto, produto in produtos_mencionados
                if produto is not None and pos_produto <= pos_cidade
            ]
            if produtos_anteriores:
                posicao_mais_recente = max(pos for pos, _ in produtos_anteriores)
                produto = min(
                    (produto for pos, produto in produtos_anteriores if pos == posicao_mais_recente),
                    key=lambda item: item.id,
                )
            else:
                produto = produto_principal
            if produto is None:
                continue
            pares.append({"cod_ibge": cidade.cod_ibge, "produto_id": produto.id})

        if len(pares) < 2:
            pares_padrao = self._pares_mock_padrao()
            print(f"[LLMService] Mock ativo: pares insuficientes; usando {len(pares_padrao)} pares padrão do CSV.")
            return self._reordenar_partida(pares_padrao, mensagem)

        print(f"[LLMService] Mock ativo: {len(pares)} par(es) inferido(s) localmente.")
        return self._reordenar_partida(pares, mensagem)


    # ---------------------------------------------------------------------------
    # Interpretação da mensagem via ChatGPT
    # ---------------------------------------------------------------------------

    def interpretar_mensagem(self, mensagem: str) -> list[dict[str, int]]:
        """
        Interpreta a mensagem em linguagem natural via ChatGPT com function calling
        e retorna a lista de pares (cod_ibge, produto_id) a serem visitados.

        O modelo pesquisa municípios e produtos nas funções locais antes de recorrer
        ao próprio conhecimento. O loop de tool calling continua até que o modelo
        emita uma resposta final (finish_reason != 'tool_calls').

        Parâmetros
        ----------
        mensagem : str
            Texto livre descrevendo a rota de entrega (ex.: "Monte uma rota para
            entrega de vacinas da Covid 19 em todas as cidades da região metropolitana
            do estado do Rio de Janeiro").

        Retorna
        -------
        list[dict[str, int]]
            Lista de {"cod_ibge": int, "produto_id": int}.
            Lista vazia se nenhum par válido for encontrado.
        """
        if self._settings.LLM_MOCK:
            return self._interpretar_mensagem_mock(mensagem)

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self._SYSTEM_PROMPT},
            {"role": "user", "content": mensagem},
        ]

        choice = None
        tokens_prompt_total = 0
        tokens_completion_total = 0
        iteracao = 0

        while True:
            iteracao += 1
            response = self._get_client().chat.completions.create(
                model=self._settings.MODELO_RESPOSTA,
                messages=messages,
                tools=self._TOOLS,
                tool_choice="auto",
            )
            choice = response.choices[0]

            uso = response.usage
            tokens_prompt_total += uso.prompt_tokens
            tokens_completion_total += uso.completion_tokens

            tipo = "tool_calls" if choice.finish_reason == "tool_calls" else "resposta final"
            tools_chamadas = (
                ", ".join(tc.function.name for tc in choice.message.tool_calls)
                if choice.finish_reason == "tool_calls"
                else "—"
            )
            print('CONSUMO DE TOKENS NA CHAMADA AO LLM:')
            print(
                f"[LLMService] iteração {iteracao} ({tipo}) | "
                f"tools: {tools_chamadas} | "
                f"prompt={uso.prompt_tokens} | "
                f"completion={uso.completion_tokens} | "
                f"total={uso.total_tokens}"
            )

            if choice.finish_reason != "tool_calls":
                break

            # Registra a resposta do assistente com as tool_calls
            messages.append(choice.message)

            # Executa cada ferramenta solicitada e devolve o resultado
            for tool_call in choice.message.tool_calls:
                resultado = self._executar_ferramenta(
                    tool_call.function.name,
                    json.loads(tool_call.function.arguments),
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(resultado, ensure_ascii=False),
                    }
                )

        print(
            f"[LLMService] TOTAL ({iteracao} iterações) | "
            f"prompt={tokens_prompt_total} | "
            f"completion={tokens_completion_total} | "
            f"total={tokens_prompt_total + tokens_completion_total}"
        )

        if choice is None:
            return []

        try:
            conteudo = choice.message.content or "[]"
            resultado = json.loads(conteudo)
            if isinstance(resultado, list):
                pares = [
                    item
                    for item in resultado
                    if isinstance(item, dict)
                    and "cod_ibge" in item
                    and "produto_id" in item
                ]
                return self._reordenar_partida(pares, mensagem)
        except json.JSONDecodeError:
            pass

        return []
