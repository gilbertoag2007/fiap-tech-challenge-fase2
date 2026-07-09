
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


class Settings:
    CORS_ORIGINS: list[str] = ["*"]
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MODELO_RESPOSTA: str = os.getenv("MODELO_CHAT", "gpt-4.1-nano")
    LLM_MOCK: bool = os.getenv("LLM_MOCK", "0").strip().lower() in {"1", "true", "sim", "yes", "on"}
    AUTH_USUARIO: str = os.getenv("AUTH_USUARIO", "")
    AUTH_SENHA: str = os.getenv("AUTH_SENHA", "")
