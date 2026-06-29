"""
Arquivo de teste manual dos services.
Execute diretamente: python teste_services.py
"""

import sys
import os

# Garante que o Python encontre os módulos do projeto
sys.path.insert(0, os.path.dirname(__file__))

from services.cidade_service import cidade_service
from services.produto_service import produto_service
from services.llm_service import LLMService
from services.rota_service import RotaService


# ===========================================================================
# Utilitário
# ===========================================================================

def secao(titulo: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {titulo}")
    print('=' * 60)

def ok(label: str, valor) -> None:
    print(f"  [OK] {label}: {valor}")

def nenhum(label: str) -> None:
    print(f"  [--] {label}: nenhum resultado")


# ===========================================================================
# Testes de CidadeService
# ===========================================================================

def testar_cidade_service():
    secao("CidadeService")

    # pesquisar_por_nome
    resultado = cidade_service.pesquisar_por_nome("Duque de Caxias")
    if resultado:
        ok("pesquisar_por_nome('Duque de Caxias')", f"{len(resultado)} cidade(s) — 1ª: {resultado[0].nome} ({resultado[0].cod_ibge})")
    else:
        nenhum("pesquisar_por_nome('Duque de Caxias')")

    # buscar_por_cod_ibge
    cidade = cidade_service.buscar_por_cod_ibge(3301702)  # Duque de Caxias-RJ
    if cidade:
        ok("buscar_por_cod_ibge(3301702)", f"{cidade.nome} / {cidade.uf}")
    else:
        nenhum("buscar_por_cod_ibge(3301702)")

    # listar_por_uf
    resultado = cidade_service.listar_por_uf("RJ")
    ok("listar_por_uf('RJ')", f"{len(resultado)} cidade(s)")

    # listar_por_regiao_tradicional sem UF
    resultado = cidade_service.listar_por_regiao_tradicional("Região Lagos")
    if resultado:
        ok("listar_por_regiao_tradicional('Região Lagos')", f"{len(resultado)} cidade(s) — 1ª: {resultado[0].nome} | região: {resultado[0].regiao_tradicional}")
    else:
        nenhum("listar_por_regiao_tradicional('Lagos')")

    # listar_por_regiao_tradicional com UF
    resultado = cidade_service.listar_por_regiao_tradicional("Região dos Lagos", uf="RJ")
    if resultado:
        ok("listar_por_regiao_tradicional('Região dos Lagos', uf='RJ')", f"{len(resultado)} cidade(s)")
    else:
        nenhum("listar_por_regiao_tradicional('Região dos Lagos', uf='RJ')")


# ===========================================================================
# Testes de ProdutoService
# ===========================================================================

def testar_produto_service():
    secao("ProdutoService")

    # listar_todos
    todos = produto_service.listar_todos()
    ok("listar_todos()", f"{len(todos)} produto(s)")
    for p in todos[:3]:
        print(f"       id={p.id} | {p.nome} | prioridade={p.prioridade}")

    # buscar_por_id
    produto = produto_service.buscar_por_id(1)
    if produto:
        ok("buscar_por_id(1)", f"{produto.nome} (prioridade={produto.prioridade})")
    else:
        nenhum("buscar_por_id(1)")

    # pesquisar_por_nome
    resultado = produto_service.pesquisar_por_nome("vacina")
    if resultado:
        ok("pesquisar_por_nome('vacina')", f"{len(resultado)} produto(s) — 1º: {resultado[0].nome}")
    else:
        nenhum("pesquisar_por_nome('vacina')")


# ===========================================================================
# Testes de CidadeService.montar_cidades_com_produtos
# ===========================================================================

def testar_montar_cidades_com_produtos():
    secao("CidadeService.montar_cidades_com_produtos")

    pares = [
        {"cod_ibge": 3301702, "produto_id": 1},   # Duque de Caxias + produto 1
        {"cod_ibge": 3304557, "produto_id": 2},   # Rio de Janeiro + produto 2
        {"cod_ibge": 9999999, "produto_id": 1},   # cod_ibge inexistente — deve ser ignorado
        {"cod_ibge": 3301702, "produto_id": 999},  # produto_id inexistente — deve ser ignorado
    ]

    resultado = cidade_service.montar_cidades_com_produtos(pares)
    ok("montar_cidades_com_produtos", f"{len(resultado)} cidade(s) válida(s) (esperado: 2)")
    for c in resultado:
        print(f"       {c.nome} ({c.cod_ibge}) → {c.produto.nome} (prioridade={c.produto.prioridade})")


# ===========================================================================
# Teste de LLMService
# ===========================================================================

def testar_llm_service():
    secao("LLMService.interpretar_mensagem")

    mensagem = (
        "Monte uma rota para entrega de vacinas da Covid 19 nos municípios "
        "Duque de Caxias, Teresópolis e seringas para São Gonçalo e Macaé."
    )
    print(f"  mensagem: \"{mensagem}\"")

    pares = LLMService().interpretar_mensagem(mensagem)
    ok("pares retornados", len(pares))
    for p in pares:
        print(f"       cod_ibge={p['cod_ibge']} | produto_id={p['produto_id']}")


# ===========================================================================
# Teste de RotaService
# ===========================================================================

def testar_rota_service():
    secao("RotaService.calcular_rota")

    resultado = RotaService().calcular_rota(
        mensagem="Monte uma rota para entrega de vacinas da Covid 19 nos municípios Duque de Caxias e Teresópolis.",
        epocas=10,
        elitismo=1,
        grau_mutacao=2.5,
        populacao_apenas_aleatoria=1,
        tamanho_populacao=20,
        tamanho_elite=5,
    )
    ok("type", resultado.get("type"))
    ok("features", len(resultado.get("features", [])))


# ===========================================================================
# Entrada principal — comente os testes que não quiser executar
# ===========================================================================

if __name__ == "__main__":
    testar_cidade_service()
    #testar_produto_service()
    #testar_montar_cidades_com_produtos()
    #testar_llm_service()        # faz chamada real à API do ChatGPT
    #testar_rota_service()       # faz chamada real à API do ChatGPT