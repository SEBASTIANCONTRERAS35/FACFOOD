"""Pasarela de prueba que se comporta como Stripe (redirige y avisa por webhook) sin red.

La "firma" es un valor fijo: aquí se prueba la lógica del checkout, no la criptografía. La
verificación real de la firma de Stripe se prueba en tests/unit/test_pago_stripe.py.
"""

import json
from decimal import Decimal

from app.ports.pagos import EventoDePago, FirmaInvalida, PasarelaNoDisponible, SesionDePago

FIRMA_VALIDA = "firma-de-prueba"


class PasarelaFalsa:
    nombre = "stripe"
    redirige = True

    def __init__(self):
        self.sesiones: dict[str, dict] = {}
        self.falla = False

    def crear_sesion(self, *, pago_id, orden_id, monto, descripcion, correo, url_exito, url_cancelar, expira_en):
        if self.falla:
            raise PasarelaNoDisponible("No se pudo iniciar el pago con tarjeta")
        ref = f"cs_test_{pago_id}"
        self.sesiones[ref] = {"orden_id": orden_id, "monto": monto, "estado": "open", "url_exito": url_exito,
                              "url_cancelar": url_cancelar, "descripcion": descripcion, "correo": correo}
        return SesionDePago(ref, f"https://checkout.stripe.test/{ref}")

    def cancelar_sesion(self, referencia):
        sesion = self.sesiones[referencia]
        if sesion["estado"] == "complete":
            return False
        sesion["estado"] = "expired"
        return True

    def leer_evento(self, cuerpo, firma):
        if firma != FIRMA_VALIDA:
            raise FirmaInvalida("Firma inválida")
        d = json.loads(cuerpo)
        return EventoDePago(d["id"], d["tipo"], d.get("referencia"), d.get("orden_id"),
                            Decimal(d["monto"]) if d.get("monto") else None, d.get("moneda", "mxn"))

    # ---- Ayudas para las pruebas ----
    def ultima(self) -> str:
        return list(self.sesiones)[-1]

    def aviso(self, referencia, tipo="pagado", monto=None, orden_id=None, moneda="mxn", evento_id=None) -> bytes:
        s = self.sesiones[referencia]
        if tipo == "pagado":
            s["estado"] = "complete"
        return json.dumps({
            "id": evento_id or f"evt_{referencia}_{tipo}", "tipo": tipo, "referencia": referencia,
            "orden_id": orden_id if orden_id is not None else s["orden_id"],
            "monto": str(monto if monto is not None else s["monto"]), "moneda": moneda,
        }).encode()
