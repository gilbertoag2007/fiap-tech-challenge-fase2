import json
from typing import Any
from openai import OpenAI
from config.settings import Settings
from services.cidade_service import cidade_service
from services.produto_service import produto_service

class LLMService:

    _settings = Settings()
    _client = OpenAI(api_key=_settings.OPENAI_API_KEY)

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
    - Caso não encontre o código IBGE pelas funções locais, utilize seu conhecimento para inferir.

    Para identificar os produtos, utilize a função pesquisar_produto_por_nome para cada produto
    mencionado na mensagem.

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
    ]


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
        return []


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
            response = self._client.chat.completions.create(
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
                return [
                    item
                    for item in resultado
                    if isinstance(item, dict)
                    and "cod_ibge" in item
                    and "produto_id" in item
                ]
        except json.JSONDecodeError:
            pass

        return []


