"""Prueba PostgreSQL de EntregaRepo.

SEGURIDAD: fabrica_entregas_pg ejecuta TRUNCATE sobre las tablas del esquema.
Solo se ejecuta si DATABASE_URL apunta a una base cuyo nombre sea exactamente
facfood_test Y FACFOOD_ALLOW_DESTRUCTIVE_TEST_DB=1. Crear esa base desechable,
aplicarle las migraciones y usarla explícitamente:

PowerShell:
  $env:DATABASE_URL='postgresql+psycopg://facfood:facfood@localhost:5432/facfood_test'
  $env:FACFOOD_ALLOW_DESTRUCTIVE_TEST_DB='1'
  python -m pytest -m integracion tests/integracion/test_entregas_pg.py

No apuntar este test a la base local de desarrollo.
"""
import os
from urllib.parse import urlparse

import pytest
from sqlalchemy import text

from app.adapters.postgres.uow import UnidadDeTrabajoPostgres
from app.seed import cargar_datos_ejemplo

@pytest.fixture
def fabrica_entregas_pg(sesiones):
    database_url = os.getenv("DATABASE_URL", "")
    nombre_db = urlparse(database_url).path.rsplit("/", 1)[-1]
    if nombre_db != "facfood_test" or os.getenv("FACFOOD_ALLOW_DESTRUCTIVE_TEST_DB") != "1":
        pytest.skip("Requiere base desechable facfood_test y confirmación explícita.")
    tablas = ("entregas, facturas, orden_eventos, usos_cupon, lineas_orden, ordenes, "
              "cupones, destinos, productos, puntos_venta, usuarios")
    with sesiones() as sesion:
        sesion.execute(text(f"TRUNCATE {tablas} RESTART IDENTITY CASCADE"))
        sesion.commit()
    fabrica = lambda: UnidadDeTrabajoPostgres(sesiones)
    cargar_datos_ejemplo(fabrica)
    return fabrica

def test_entrega_repo_pg_filtra_y_persiste_asignacion(fabrica_entregas_pg):
    with fabrica_entregas_pg() as uow:
        assert [r.id for r in uow.entregas.ordenes_disponibles()] == [1, 3]
    from app.shared.auth import UsuarioActual
    from app.entregas.servicio import aceptar
    aceptar(fabrica_entregas_pg, UsuarioActual(5, "repartidor"), 1)
    with fabrica_entregas_pg() as uow:
        assert [r.id for r in uow.entregas.ordenes_disponibles()] == [3]
        assert uow.entregas.por_orden(1).repartidor_id == 5
