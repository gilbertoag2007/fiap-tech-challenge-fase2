import csv
from pathlib import Path

from models.produto import Produto


_ARQUIVO_CSV = Path(__file__).parent.parent / "data" / "produtos.csv"


class ProdutoService:
    """
    Carrega e indexa os produtos a partir do CSV.

    O arquivo é lido uma única vez na instanciação. Use a instância
    ``produto_service`` deste módulo para evitar releituras desnecessárias.
    """

    def __init__(self) -> None:
        self._produtos: list[Produto] = []
        self._indice: dict[int, Produto] = {}
        self._carregar()

    def _carregar(self) -> None:
        """Lê o CSV e popula a lista e o índice de produtos."""
        with open(_ARQUIVO_CSV, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                try:
                    produto = Produto(
                        id=int(row["ID"]),
                        nome=row["NOME"].strip(),
                        prioridade=int(row["PRIORIDADE"]),
                    )
                    self._produtos.append(produto)
                    self._indice[produto.id] = produto
                except (ValueError, KeyError):
                    continue

    def listar_todos(self) -> list[Produto]:
        """Retorna todos os produtos carregados."""
        return list(self._produtos)

    def buscar_por_id(self, produto_id: int) -> Produto | None:
        """
        Retorna o produto cujo atributo ``id`` seja igual a ``produto_id``.

        Parâmetros
        ----------
        produto_id : int — identificador do produto.

        Retorna
        -------
        Produto ou None se não encontrado.
        """
        return next((p for p in self._produtos if p.id == produto_id), None)

    def pesquisar_por_nome(self, termo: str) -> list[Produto]:
        """
        Retorna produtos cujo nome corresponda ao termo de forma parcial e bidirecional
        (insensível a maiúsculas).

        Busca bidirecional: o nome do produto está contido no termo OU o termo está
        contido no nome do produto. Isso resolve buscas onde o texto enviado é mais
        longo que o nome cadastrado (ex.: "vacina da covid 19" encontra "Vacina Covid 19")
        e também buscas com fragmentos (ex.: "seringa" encontra "Seringa Descartável").

        Parâmetros
        ----------
        termo : str — nome ou descrição do produto em linguagem natural.
        """
        busca = termo.strip().lower()
        return [
            p for p in self._produtos
            if busca in p.nome.lower() or p.nome.lower() in busca
        ]


# Instância singleton — importe e use diretamente nos routers e services.
produto_service = ProdutoService()
