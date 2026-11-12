"""Configuración de la app, leída de variables de entorno.

FACFOOD_REPOSITORIO=memoria  -> datos de ejemplo en memoria (no requiere base de datos)
FACFOOD_REPOSITORIO=postgres -> PostgreSQL + PostGIS (DATABASE_URL)
FACFOOD_PASARELA=simulado     -> pago simulado, sin cobro (por defecto)
FACFOOD_PASARELA=stripe       -> Stripe Checkout; requiere STRIPE_SECRET_KEY y STRIPE_WEBHOOK_SECRET
"""

import os
from dataclasses import dataclass
from functools import lru_cache


def _bool(nombre: str, defecto: bool) -> bool:
    valor = os.getenv(nombre)
    if valor is None:
        return defecto
    return valor.strip().lower() in {"1", "true", "si", "sí", "yes"}


def normalizar_url_bd(url: str) -> str:
    """Neon, Render y Heroku dan la URL como postgres:// o postgresql://; SQLAlchemy usaría
    psycopg2, que no está instalado. Se fuerza el controlador psycopg (v3)."""
    for prefijo in ("postgres://", "postgresql://"):
        if url.startswith(prefijo):
            return "postgresql+psycopg://" + url[len(prefijo):]
    return url


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
    pasarela: str = "simulado"
    # Secretos de Stripe: solo en variables de entorno (Render), nunca en el repositorio.
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    # A dónde regresa Stripe al comprador (éxito o cancelación).
    url_frontend: str = "http://localhost:5173"


@lru_cache
def obtener_config() -> Config:
    return Config(
        repositorio=os.getenv("FACFOOD_REPOSITORIO", "memoria"),
        database_url=normalizar_url_bd(os.getenv(
            "DATABASE_URL", "postgresql+psycopg://facfood:facfood@localhost:5432/facfood"
        )),
        jwt_secreto=os.getenv("FACFOOD_JWT_SECRETO", "solo-para-desarrollo-cambiar-en-produccion"),
        jwt_horas=int(os.getenv("FACFOOD_JWT_HORAS", "24")),
        permitir_usuario_prueba=_bool("FACFOOD_PERMITIR_USUARIO_PRUEBA", True),
        cors_origenes=tuple(
            o.strip()
            for o in os.getenv("FACFOOD_CORS", "http://localhost:5173").split(",")
            if o.strip()
        ),
        pasarela=os.getenv("FACFOOD_PASARELA", "simulado").strip().lower(),
        stripe_secret_key=os.getenv("STRIPE_SECRET_KEY") or None,
        stripe_webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET") or None,
        url_frontend=os.getenv("FACFOOD_URL_FRONTEND", "http://localhost:5173").rstrip("/"),
    )
