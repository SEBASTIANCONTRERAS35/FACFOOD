"""API de FACFOOD. Arranque: `uvicorn app.main:app --reload` (desde backend/)."""

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from app.catalogo.router import router as catalogo
from app.checkout.router import router as checkout
from app.cuentas.router import router as cuentas
from app.dev.router import router as dev
from app.entregas.router import router as entregas
from app.seguimiento.router import router as seguimiento
from app.shared.config import obtener_config
from app.shared.errores import documentar_errores, registrar_manejadores
from app.vendedor.router import router as vendedor


def create_app() -> FastAPI:
    config = obtener_config()
    app = FastAPI(
        title="FACFOOD API",
        version="0.1.0",
        description=(
            "Pedidos de comida dentro de Ciudad Universitaria. "
            "Dinero siempre como texto con 2 decimales.\n\n"
            "**Squad Kora Bits** — Negocios Electrónicos y Desarrollo Web (2027-1).\n\n"
            "Integrantes: Emilio Sebastián Contreras Colmenero, "
            "Luis Angel Garcés Hernández, José Arturo Ciriaco Vargas, "
            "Diana Sofia Romero Garcia, Oscar Saldivar Pantoja y "
            "Jose Alberto Zarco Romero.\n\n"
            "**Errores:** todos siguen RFC 7807 (`application/problem+json`): `type`, `title`, `status`, "
            "`detail`, `instance` y `codigo`. Si falla la validación de un DTO se responde **400** con "
            "`invalid_params`. Ningún error repite lo que envió el usuario. Catálogo: `docs/ERRORES.md`.\n\n"
            "**Probar como un usuario de ejemplo:** en desarrollo, encabezado `X-Usuario-Id` "
            "(1 comprador, 3 vendedor, 5 repartidor) o `Authorization: Bearer <token>` de `/auth/login`."
        ),
        contact={"name": "Squad Kora Bits"},
        openapi_tags=[
            {"name": "Cuentas", "description": "Registro (LFPDPPP), login con JWT y perfil dual · vista 01"},
            {"name": "Catálogo", "description": "Puestos cercanos con PostGIS y menú · vistas 02 y 03"},
            {"name": "Checkout", "description": "Orden, cupón o lealtad, entrega (Strategy) y pago · vista 04"},
            {"name": "Seguimiento", "description": "Estado del pedido y factura · vista 05"},
            {"name": "Vendedor", "description": "Panel del puesto · vista 06"},
            {"name": "Entregas", "description": "Modo repartidor · vistas 07 y 08"},
            {"name": "Sistema", "description": "Salud del servicio"},
        ],
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

    @app.get("/api-docs", include_in_schema=False)
    def api_docs():
        return RedirectResponse("/docs")

    @app.get("/salud", tags=["Sistema"])
    def salud():
        return {"estado": "ok", "repositorio": config.repositorio}

    documentar_errores(app)
    return app


app = create_app()
