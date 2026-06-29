
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


class Settings:
    CORS_ORIGINS: list[str] = ["*"]
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MODELO_RESPOSTA: str = os.getenv("MODELO_CHAT", "gpt-4.1-nano")
