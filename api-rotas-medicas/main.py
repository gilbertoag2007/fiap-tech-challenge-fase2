from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import Settings
from api.routers import cidade, produto, rotas

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

app.include_router(cidade.router)
app.include_router(produto.router)
app.include_router(rotas.router)



@app.get("/health", tags=["Health"])
def health_check():
    """Verifica se a API está no ar."""
    return {"status": "ok", "versao": "1.0.0"}

