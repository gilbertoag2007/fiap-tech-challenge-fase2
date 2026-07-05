from fastapi import Header, HTTPException

from services.auth_service import auth_service


def verificar_token(authorization: str | None = Header(default=None)) -> str:
    """
    Dependência do FastAPI que exige um header `Authorization: Bearer <token>`
    válido e não expirado, lançando 401 caso contrário.

    Parâmetros
    ----------
    authorization : str | None
        Header HTTP no formato "Bearer <token>".

    Retorna
    -------
    str — o token validado (útil para o endpoint de logout revogá-lo).
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Não autenticado. Faça login novamente.")

    token = authorization.removeprefix("Bearer ").strip()
    if not auth_service.validar_token(token):
        raise HTTPException(status_code=401, detail="Sessão expirada ou inválida. Faça login novamente.")

    return token
