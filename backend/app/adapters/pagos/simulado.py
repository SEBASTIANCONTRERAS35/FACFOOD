"""Pasarela simulada: no cobra. El comprador confirma con POST /ordenes/{id}/pagar."""

import secrets

from app.ports.pagos import EventoDePago, FirmaInvalida, SesionDePago


class PagoSimulado:
    nombre = "simulado"
    redirige = False

    def crear_sesion(self, **_) -> SesionDePago:
        return SesionDePago(referencia=f"sim_{secrets.token_hex(8)}", url=None)

    def cancelar_sesion(self, referencia: str) -> bool:
        return True

    def leer_evento(self, cuerpo: bytes, firma: str | None) -> EventoDePago:
        # El simulado no recibe avisos externos: cualquier llamada al webhook se rechaza.
        raise FirmaInvalida("La pasarela simulada no acepta avisos")
