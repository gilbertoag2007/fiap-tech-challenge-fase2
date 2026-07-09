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
                        peso_kg=float(row.get("PESO_KG") or 0.0),
                    )
                    self._produtos.append(produto)
                    self._indice[produto.id] = produto
                except (ValueError, KeyError):
                    continue

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

        Estratégia em duas camadas:
        1. Substring bidirecional exata (ex.: "seringa" encontra "Seringa Descartável").
        2. Prefixo por palavras: TODA palavra significativa (> 2 chars) do termo de busca
           precisa corresponder, por prefixo em qualquer direção, a alguma palavra do nome
           do produto. Isso resolve flexões como "vacinas" encontrando "Vacina da Covid"
           (pt="vacinas", pn="vacina" → "vacinas".startswith("vacina") == True), sem permitir
           que uma única palavra genérica em comum (ex.: "vacina") faça termos mais específicos
           como "vacina covid" corresponderem a produtos não relacionados como "Vacina da Gripe".

        Parâmetros
        ----------
        termo : str — nome ou descrição do produto em linguagem natural.
        """
        busca = termo.strip().lower()
        palavras_busca = [w for w in busca.split() if len(w) > 2]

        def _corresponde(nome_lower: str) -> bool:
            if busca in nome_lower or nome_lower in busca:
                return True
            if not palavras_busca:
                return False
            palavras_nome = [w for w in nome_lower.split() if len(w) > 2]
            return all(
                any(pt.startswith(pn) or pn.startswith(pt) for pn in palavras_nome)
                for pt in palavras_busca
            )

        return [p for p in self._produtos if _corresponde(p.nome.lower())]


# Instância singleton — importe e use diretamente nos routers e services.
produto_service = ProdutoService()
