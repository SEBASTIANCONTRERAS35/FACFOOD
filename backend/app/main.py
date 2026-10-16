"""API de FACFOOD. Arranque: `uvicorn app.main:app --reload` (desde backend/)."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.catalogo.router import router as catalogo
from app.checkout.router import router as checkout
from app.cuentas.router import router as cuentas
from app.dev.router import router as dev
from app.entregas.router import router as entregas
from app.seguimiento.router import router as seguimiento
from app.shared.config import obtener_config
from app.shared.errores import registrar_manejadores
from app.vendedor.router import router as vendedor


def create_app() -> FastAPI:
    config = obtener_config()
    app = FastAPI(
        title="FACFOOD API",
        version="0.1.0",
        description="Pedidos de comida dentro de Ciudad Universitaria. Dinero siempre como texto con 2 decimales.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(config.cors_origenes),
        allow_methods=["*"],
        allow_headers=["*"],
    )
    registrar_manejadores(app)

    # Sebastián: vistas 01–04
    app.include_router(cuentas)
    app.include_router(catalogo)
    app.include_router(checkout)
    # Arturo: vistas 05–08
    app.include_router(seguimiento)
    app.include_router(vendedor)
    app.include_router(entregas)

    if config.permitir_usuario_prueba:
        app.include_router(dev)

    @app.get("/salud", tags=["Sistema"])
    def salud():
        return {"estado": "ok", "repositorio": config.repositorio}

    return app


app = create_app()
