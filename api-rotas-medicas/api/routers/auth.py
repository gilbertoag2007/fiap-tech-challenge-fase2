import time

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import verificar_token
from api.schemas.auth import LoginRequest, LoginResponse
from services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["Autenticação"])

# Atraso fixo aplicado a TODA tentativa de login (sucesso ou falha). Roda no
# backend (não dá para contornar chamando a API diretamente, diferente de um
# atraso no frontend) e dificulta força bruta automatizada. Aplicado também
# em logins bem-sucedidos para não vazar, pela diferença de tempo de resposta,
# se o usuário informado existe mas a senha está errada.
_DELAY_LOGIN_SEGUNDOS = 1.0


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest) -> LoginResponse:
    """Autentica com usuário/senha fixos (definidos no .env) e retorna um token de sessão."""
    time.sleep(_DELAY_LOGIN_SEGUNDOS)

    resultado = auth_service.autenticar(request.usuario, request.senha)
    if resultado is None:
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos.")

    return LoginResponse(**resultado)


@router.post("/logout")
def logout(token: str = Depends(verificar_token)) -> dict[str, str]:
    """Revoga o token de sessão atual."""
    auth_service.revogar_token(token)
    return {"status": "ok"}
