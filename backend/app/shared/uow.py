"""Elige el adaptador de persistencia según la configuración (memoria o postgres).

Los routers piden `fabrica: FabricaUoW = Depends(obtener_fabrica_uow)` y abren
una transacción con `with fabrica() as uow: ...`. Las pruebas reemplazan esta
dependencia con app.dependency_overrides.
"""

from collections.abc import Callable
from functools import lru_cache

from app.ports.repositorios import UnidadDeTrabajo
from app.shared.config import obtener_config

FabricaUoW = Callable[[], UnidadDeTrabajo]


@lru_cache
def _fabrica_memoria() -> FabricaUoW:
    from app.adapters.memoria.uow import AlmacenMemoria, UnidadDeTrabajoMemoria
    from app.seed import cargar_datos_ejemplo

    almacen = AlmacenMemoria()
    fabrica = lambda: UnidadDeTrabajoMemoria(almacen)  # noqa: E731
    cargar_datos_ejemplo(fabrica)
    return fabrica


@lru_cache
def _fabrica_postgres(database_url: str) -> FabricaUoW:
    from app.adapters.postgres.uow import UnidadDeTrabajoPostgres, crear_fabrica_sesiones

    sesiones = crear_fabrica_sesiones(database_url)
    return lambda: UnidadDeTrabajoPostgres(sesiones)


def obtener_fabrica_uow() -> FabricaUoW:
    config = obtener_config()
    if config.repositorio == "postgres":
        return _fabrica_postgres(config.database_url)
    return _fabrica_memoria()
