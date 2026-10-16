"""Configuración de la app, leída de variables de entorno.

FACFOOD_REPOSITORIO=memoria  -> datos de ejemplo en memoria (no requiere base de datos)
FACFOOD_REPOSITORIO=postgres -> PostgreSQL + PostGIS (DATABASE_URL)
"""

import os
from dataclasses import dataclass
from functools import lru_cache


def _bool(nombre: str, defecto: bool) -> bool:
    valor = os.getenv(nombre)
    if valor is None:
        return defecto
    return valor.strip().lower() in {"1", "true", "si", "sí", "yes"}


@dataclass(frozen=True)
class Config:
    repositorio: str
    database_url: str
    jwt_secreto: str
    jwt_horas: int
    # Encabezado X-Usuario-Id para entrar como un usuario de ejemplo sin login.
    # Solo para desarrollo: en producción debe ser False.
    permitir_usuario_prueba: bool
    cors_origenes: tuple[str, ...]


@lru_cache
def obtener_config() -> Config:
    return Config(
        repositorio=os.getenv("FACFOOD_REPOSITORIO", "memoria"),
        database_url=os.getenv(
            "DATABASE_URL", "postgresql+psycopg://facfood:facfood@localhost:5432/facfood"
        ),
        jwt_secreto=os.getenv("FACFOOD_JWT_SECRETO", "solo-para-desarrollo-cambiar-en-produccion"),
        jwt_horas=int(os.getenv("FACFOOD_JWT_HORAS", "24")),
        permitir_usuario_prueba=_bool("FACFOOD_PERMITIR_USUARIO_PRUEBA", True),
        cors_origenes=tuple(
            o.strip()
            for o in os.getenv("FACFOOD_CORS", "http://localhost:5173").split(",")
            if o.strip()
        ),
    )
