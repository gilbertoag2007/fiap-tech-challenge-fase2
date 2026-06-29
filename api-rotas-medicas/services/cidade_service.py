import csv
from pathlib import Path

from models.cidade import Cidade
from models.produto import Produto


_ARQUIVO_CSV = Path(__file__).parent.parent / "data" / "cidades.csv"

# Limites geográficos do Brasil usados para inferir o divisor correto
_LAT_MIN, _LAT_MAX = -35.0, -5.0
_LON_MIN, _LON_MAX = -74.0, -34.0


def _parse_coordenada(valor_str: str, min_val: float, max_val: float) -> float:
    """
    Converte o inteiro armazenado no CSV para graus decimais.

    O CSV omite o ponto decimal (ex.: -119283 → -11.9283).
    O divisor correto é inferido pelo intervalo geográfico válido.

    Parâmetros
    ----------
    valor_str : str
        Valor bruto lido do CSV.
    min_val : float
        Limite inferior do intervalo válido para a coordenada.
    max_val : float
        Limite superior do intervalo válido para a coordenada.

    Retorna
    -------
    float — coordenada em graus decimais.

    Raises
    ------
    ValueError
        Se nenhum divisor produzir um valor dentro do intervalo válido.
    """
    num = int(valor_str.strip())
    for divisor in (10_000, 1_000, 100_000, 100):
        candidato = num / divisor
        if min_val <= candidato <= max_val:
            return candidato
    raise ValueError(
        f"Não foi possível converter '{valor_str}' para uma coordenada "
        f"no intervalo [{min_val}, {max_val}]."
    )


class CidadeService:
    """
    Carrega e indexa os municípios brasileiros a partir do CSV do IBGE.

    O arquivo é lido uma única vez na instanciação. Use a instância
    ``municipio_service`` deste módulo para evitar releituras desnecessárias.
    """

    def __init__(self) -> None:
        self._cidades: list[Cidade] = []
        self._indice: dict[int, Cidade] = {}
        self._carregar()

    # ------------------------------------------------------------------
    # Carga
    # ------------------------------------------------------------------

    def _carregar(self) -> None:
        """Lê o CSV e popula a lista e o índice de cidades."""
        with open(_ARQUIVO_CSV, encoding="latin-1", newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                try:
                    regiao = row.get("REGIAO_TRADICIONAL", "").strip() or None
                    cidade = Cidade(
                        cod_ibge=int(row["COD_IBGE"]),
                        nome=row["NOME"].strip(),
                        uf=row["UF"].strip(),
                        latitude=_parse_coordenada(row["LATITUDE"], _LAT_MIN, _LAT_MAX),
                        longitude=_parse_coordenada(row["LONGITUDE"], _LON_MIN, _LON_MAX),
                        regiao_tradicional=regiao,
                    )
                    self._cidades.append(cidade)
                    self._indice[cidade.cod_ibge] = cidade
                except (ValueError, KeyError):
                    continue

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------

    def listar_todas(self) -> list[Cidade]:
        """Retorna todas as cidades carregadas."""
        return list(self._cidades)

    def listar_por_uf(self, uf: str) -> list[Cidade]:
        """
        Retorna cidades filtradas pela UF.

        Parâmetros
        ----------
        uf : str — sigla do estado (ex.: "SP"), insensível a maiúsculas.
        """
        uf_upper = uf.strip().upper()
        return [c for c in self._cidades if c.uf == uf_upper]

    def buscar_por_cod_ibge(self, cod_ibge: int) -> Cidade | None:
        """
        Retorna a cidade com o código IBGE informado.

        Parâmetros
        ----------
        cod_ibge : int

        Retorna
        -------
        Cidade ou None se não encontrada.
        """
        return self._indice.get(cod_ibge)

    def listar_por_regiao_tradicional(
        self,
        regiao: str,
        uf: str | None = None,
    ) -> list[Cidade]:
        """
        Retorna cidades cujo campo regiao_tradicional contenha todas as palavras
        do termo informado (busca parcial, insensível a maiúsculas).
        Quando ``uf`` for fornecida, filtra também pelo estado.

        Exemplos
        --------
        "Região do Lagos", uf="RJ"  →  encontra "Região dos Lagos / Costa do Sol" em RJ
        "metropolitana"             →  encontra regiões metropolitanas de qualquer UF

        Parâmetros
        ----------
        regiao : str       — nome ou fragmento da região tradicional.
        uf     : str|None  — sigla do estado (ex.: "RJ"). Opcional.
        """
        busca = regiao.strip().lower()
        uf_upper = uf.strip().upper() if uf else None

        # Busca bidirecional: o campo está contido na busca OU a busca está contida no campo.
        # Isso resolve datasets com valores curtos (ex.: "Metropolitana") pesquisados com
        # textos longos (ex.: "Região Metropolitana do Rio de Janeiro"), e vice-versa.
        cidades_encontradas = [
            c for c in self._cidades
            if c.regiao_tradicional is not None
            and (busca in c.regiao_tradicional.lower() or c.regiao_tradicional.lower() in busca)
            and (uf_upper is None or c.uf == uf_upper)
        ]

        print(f"Cidades Encontradas na região '{regiao}' (UF: {uf}): {len(cidades_encontradas)} cidade(s)")
        return cidades_encontradas

    def pesquisar_por_nome(self, termo: str) -> list[Cidade]:
        """
        Retorna cidades cujo nome contém o termo (insensível a maiúsculas).

        Parâmetros
        ----------
        termo : str — nome ou fragmento do nome da cidade.
        """
        termo_lower = termo.strip().lower()
        return [c for c in self._cidades if termo_lower in c.nome.lower()]

    def montar_cidades_com_produtos(
        self,
        pares: list[dict[str, int]],
    ) -> list[Cidade]:
        """
        Monta uma lista de Cidades com produtos atribuídos a partir de pares
        (cod_ibge, produto_id).

        Para cada par válido, localiza a cidade pelo código IBGE e o produto
        pelo ID, e retorna uma nova instância de Cidade com o produto atribuído.
        Pares cujo cod_ibge ou produto_id não sejam encontrados são ignorados.

        Parâmetros
        ----------
        pares : list[dict[str, int]]
            Lista de dicionários com as chaves ``cod_ibge`` e ``produto_id``.

        Retorna
        -------
        list[Cidade] — cidades com produto preenchido, na mesma ordem dos pares válidos.
        """
        from services.produto_service import produto_service  # import local evita dependência circular entre singletons

        resultado: list[Cidade] = []
        for par in pares:
            cod_ibge = par.get("cod_ibge")
            produto_id = par.get("produto_id")
            if cod_ibge is None or produto_id is None:
                continue

            cidade_base = self._indice.get(cod_ibge)
            produto = produto_service.buscar_por_id(produto_id)
            if cidade_base is None or produto is None:
                continue

            cidade_com_produto = Cidade(
                cod_ibge=cidade_base.cod_ibge,
                nome=cidade_base.nome,
                uf=cidade_base.uf,
                latitude=cidade_base.latitude,
                longitude=cidade_base.longitude,
                regiao_tradicional=cidade_base.regiao_tradicional,
                produto=produto,
            )
            resultado.append(cidade_com_produto)

        return resultado


# Instância singleton — importe e use diretamente nos routers e services.
cidade_service = CidadeService()