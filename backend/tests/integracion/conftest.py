"""Pruebas contra PostgreSQL + PostGIS reales.

Se ejecutan en la CI (servicio postgis) o localmente con:
    docker compose up -d db
    DATABASE_URL=postgresql+psycopg://facfood:facfood@localhost:5432/facfood alembic upgrade head
    DATABASE_URL=... pytest -m integracion
Sin DATABASE_URL se omiten.
"""

import os

import pytest
from sqlalchemy import text

from app.seed import cargar_datos_ejemplo

DATABASE_URL = os.getenv("DATABASE_URL")

TABLAS = ("entregas, facturas, orden_eventos, usos_cupon, lineas_orden, ordenes, "
          "cupones, destinos, productos, puntos_venta, usuarios")


def pytest_collection_modifyitems(items):
    for item in items:
        if "integracion" in str(item.fspath):
            item.add_marker(pytest.mark.integracion)
            if not DATABASE_URL:
                item.add_marker(pytest.mark.skip(reason="Requiere DATABASE_URL (PostgreSQL)"))


@pytest.fixture(scope="session")
def sesiones():
    from app.adapters.postgres.uow import crear_fabrica_sesiones

    return crear_fabrica_sesiones(DATABASE_URL)


@pytest.fixture
def fabrica_pg(sesiones):
    """Base limpia con los datos de ejemplo para cada prueba."""
    from app.adapters.postgres.uow import UnidadDeTrabajoPostgres

    with sesiones() as s:
        s.execute(text(f"TRUNCATE {TABLAS} RESTART IDENTITY CASCADE"))
        s.commit()
    f = lambda: UnidadDeTrabajoPostgres(sesiones)  # noqa: E731
    cargar_datos_ejemplo(f)
    return f
