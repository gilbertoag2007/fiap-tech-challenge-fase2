import secrets
import time

from config.settings import Settings


class AuthService:
    """
    Autenticação simples com usuário/senha únicos (fixos via .env) e token
    aleatório mantido em memória — sem persistência em banco, adequada a um
    projeto com um único usuário/sessão administrativa.

    Notas
    -----
    Os tokens emitidos existem apenas em memória: reiniciar o processo da API
    invalida todas as sessões ativas. Isso é aceitável dado o escopo do
    projeto (um único usuário fixo, sem necessidade de persistir sessões
    entre reinícios).
    """

    TOKEN_TTL_SEGUNDOS: int = 30 * 60  # 30 minutos

    def __init__(self) -> None:
        self._tokens: dict[str, float] = {}  # token -> instante de expiração (epoch)

    def autenticar(self, usuario: str, senha: str) -> dict[str, object] | None:
        """
        Valida usuário/senha contra as credenciais fixas do .env e, se
        corretas, emite um novo token de sessão aleatório.

        Parâmetros
        ----------
        usuario : str
        senha : str

        Retorna
        -------
        dict com "token" (str) e "expires_in" (int, segundos) se as
        credenciais forem válidas; None caso contrário (incluindo o caso de
        AUTH_USUARIO/AUTH_SENHA não estarem configurados no .env).
        """
        settings = Settings()
        if not settings.AUTH_USUARIO or not settings.AUTH_SENHA:
            return None
        if usuario != settings.AUTH_USUARIO or senha != settings.AUTH_SENHA:
            return None

        token = secrets.token_urlsafe(32)
        self._tokens[token] = time.time() + self.TOKEN_TTL_SEGUNDOS
        return {"token": token, "expires_in": self.TOKEN_TTL_SEGUNDOS}

    def validar_token(self, token: str | None) -> bool:
        """
        Verifica se `token` existe e ainda não expirou.

        Remove o token do armazenamento caso já tenha expirado (limpeza
        preguiçosa — evita crescer indefinidamente o dicionário em memória).
        """
        if not token:
            return False
        expira_em = self._tokens.get(token)
        if expira_em is None:
            return False
        if time.time() >= expira_em:
            self._tokens.pop(token, None)
            return False
        return True

    def revogar_token(self, token: str | None) -> None:
        """Remove o token (logout). Não faz nada se o token não existir."""
        if token:
            self._tokens.pop(token, None)


# Instância singleton — importe e use diretamente nos routers.
auth_service = AuthService()
