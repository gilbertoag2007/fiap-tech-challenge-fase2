import sys

# Força line-buffering no stdout/stderr: em containers (Render, Docker etc.), a saída
# não é um terminal interativo, então o Python usa buffering em bloco por padrão — os
# prints só aparecem no log quando o buffer enche ou o processo termina, dando a falsa
# impressão de que tudo aconteceu "instantaneamente" no mesmo instante. Line-buffering
# faz cada linha aparecer no log assim que é impressa, com timestamp real.
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import Settings
from api.routers import auth, rotas

app = FastAPI(
    title="API — Rotas Médicas",
    description="Otimização de rotas de entrega de medicamentos e insumos via Algoritmos Genéticos.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=Settings().CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(rotas.router)



@app.get("/health", tags=["Health"])
def health_check():
    """Verifica se a API está no ar."""
    return {"status": "ok", "versao": "1.0.0"}

