"""
Testes de services/auth_service.py

Estratégia: cada teste cria sua própria instância de AuthService (não o
singleton do módulo) para isolar o dicionário de tokens em memória entre
testes, e usa monkeypatch para controlar as credenciais válidas sem depender
do .env real.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import Settings
from services.auth_service import AuthService


@pytest.fixture
def credenciais_validas(monkeypatch):
    monkeypatch.setattr(Settings, "AUTH_USUARIO", "admin", raising=False)
    monkeypatch.setattr(Settings, "AUTH_SENHA", "segredo123", raising=False)


def test_autenticar_com_credenciais_corretas_retorna_token(credenciais_validas):
    auth = AuthService()
    resultado = auth.autenticar("admin", "segredo123")

    assert resultado is not None
    assert isinstance(resultado["token"], str) and len(resultado["token"]) > 20
    assert resultado["expires_in"] == auth.TOKEN_TTL_SEGUNDOS


def test_autenticar_com_senha_errada_retorna_none(credenciais_validas):
    auth = AuthService()
    assert auth.autenticar("admin", "senha_errada") is None


def test_autenticar_com_usuario_errado_retorna_none(credenciais_validas):
    auth = AuthService()
    assert auth.autenticar("outro_usuario", "segredo123") is None


def test_autenticar_sem_credenciais_configuradas_retorna_none(monkeypatch):
    monkeypatch.setattr(Settings, "AUTH_USUARIO", "", raising=False)
    monkeypatch.setattr(Settings, "AUTH_SENHA", "", raising=False)
    auth = AuthService()
    assert auth.autenticar("admin", "segredo123") is None


def test_tokens_gerados_sao_unicos_por_login(credenciais_validas):
    auth = AuthService()
    token1 = auth.autenticar("admin", "segredo123")["token"]
    token2 = auth.autenticar("admin", "segredo123")["token"]
    assert token1 != token2


def test_validar_token_recem_emitido_retorna_true(credenciais_validas):
    auth = AuthService()
    token = auth.autenticar("admin", "segredo123")["token"]
    assert auth.validar_token(token) is True


def test_validar_token_inexistente_retorna_false():
    auth = AuthService()
    assert auth.validar_token("token-que-nunca-existiu") is False


def test_validar_token_none_ou_vazio_retorna_false():
    auth = AuthService()
    assert auth.validar_token(None) is False
    assert auth.validar_token("") is False


def test_validar_token_expirado_retorna_false_e_remove_o_token(credenciais_validas):
    auth = AuthService()
    token = auth.autenticar("admin", "segredo123")["token"]

    # Simula expiração imediata sem depender de tempo real (sleep).
    auth.TOKEN_TTL_SEGUNDOS = -1
    auth._tokens[token] = auth._tokens[token] - 10_000

    assert auth.validar_token(token) is False
    assert token not in auth._tokens  # limpeza preguiçosa removeu o token expirado


def test_revogar_token_invalida_sessao_ativa(credenciais_validas):
    auth = AuthService()
    token = auth.autenticar("admin", "segredo123")["token"]
    assert auth.validar_token(token) is True

    auth.revogar_token(token)
    assert auth.validar_token(token) is False


def test_revogar_token_inexistente_nao_lanca_erro():
    auth = AuthService()
    auth.revogar_token("token-que-nao-existe")  # não deve lançar exceção
    auth.revogar_token(None)  # idem
