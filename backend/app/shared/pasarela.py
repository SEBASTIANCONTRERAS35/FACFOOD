"""Elige la pasarela de pago según FACFOOD_PASARELA. Las pruebas la reemplazan con
app.dependency_overrides[obtener_pasarela]."""

from functools import lru_cache

from app.ports.pagos import PasarelaDePago
from app.shared.config import obtener_config


@lru_cache
def _pasarela(nombre: str, clave: str | None, secreto: str | None) -> PasarelaDePago:
    if nombre == "simulado":
        from app.adapters.pagos.simulado import PagoSimulado

        return PagoSimulado()
    if nombre == "stripe":
        from app.adapters.pagos.stripe_checkout import PagoStripe

        # Falla al arrancar si faltan los secretos: nunca se sirve un webhook sin verificar firma.
        return PagoStripe(clave, secreto)
    raise ValueError(f"FACFOOD_PASARELA desconocida: {nombre!r} (usa simulado o stripe)")


def obtener_pasarela() -> PasarelaDePago:
    c = obtener_config()
    return _pasarela(c.pasarela, c.stripe_secret_key, c.stripe_webhook_secret)
