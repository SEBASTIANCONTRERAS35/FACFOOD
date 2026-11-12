"""Pasarela Stripe Checkout (modo de prueba). Ver ADR_004.md.

- El monto se manda en centavos MXN y sale de la orden guardada, nunca del cliente.
- El webhook se autentica con la firma de Stripe (encabezado Stripe-Signature, HMAC-SHA256
  con STRIPE_WEBHOOK_SECRET, tolerancia de 5 minutos contra repeticiones).
- La firma se verifica sobre el cuerpo crudo y el JSON se lee después: no se confía en nada
  que no haya pasado la verificación.
"""

import json
import logging
from datetime import datetime
from decimal import Decimal

import stripe

from app.ports.pagos import EventoDePago, FirmaInvalida, PasarelaNoDisponible, SesionDePago

log = logging.getLogger(__name__)

TOLERANCIA_FIRMA_S = 300

_TIPOS = {
    "checkout.session.completed": "pagado",
    "checkout.session.async_payment_succeeded": "pagado",
    "checkout.session.async_payment_failed": "fallido",
    "checkout.session.expired": "expirado",
}


def a_centavos(monto: Decimal) -> int:
    return int((monto * 100).to_integral_exact())


class PagoStripe:
    nombre = "stripe"
    redirige = True

    def __init__(self, clave_secreta: str, secreto_webhook: str, cliente: "stripe.StripeClient | None" = None):
        if not clave_secreta or not secreto_webhook:
            raise ValueError("Faltan STRIPE_SECRET_KEY o STRIPE_WEBHOOK_SECRET")
        self._secreto_webhook = secreto_webhook
        self._sesiones = (cliente or stripe.StripeClient(clave_secreta)).v1.checkout.sessions

    def crear_sesion(self, *, pago_id, orden_id, monto, descripcion, correo, url_exito, url_cancelar,
                     expira_en: datetime) -> SesionDePago:
        metadatos = {"orden_id": str(orden_id), "pago_id": str(pago_id)}
        parametros = {
            "mode": "payment",
            "payment_method_types": ["card"],
            "line_items": [{
                "quantity": 1,
                "price_data": {"currency": "mxn", "unit_amount": a_centavos(monto), "product_data": {"name": descripcion}},
            }],
            "client_reference_id": str(pago_id),
            "metadata": metadatos,
            "payment_intent_data": {"metadata": metadatos},
            "success_url": url_exito,
            "cancel_url": url_cancelar,
            "expires_at": int(expira_en.timestamp()),
        }
        if correo:
            parametros["customer_email"] = correo
        try:
            # La llave de idempotencia evita crear dos sesiones si la petición se reintenta.
            sesion = self._sesiones.create(parametros, {"idempotency_key": f"facfood-pago-{pago_id}"})
        except stripe.StripeError as exc:
            log.warning("Stripe rechazó la sesión del pago %s: %s", pago_id, type(exc).__name__)
            raise PasarelaNoDisponible("No se pudo iniciar el pago con tarjeta") from exc
        return SesionDePago(referencia=sesion.id, url=sesion.url)

    def cancelar_sesion(self, referencia: str) -> bool:
        try:
            sesion = self._sesiones.retrieve(referencia)
            if sesion.status == "complete":
                return False
            if sesion.status == "open":
                sesion = self._sesiones.expire(referencia)
            return sesion.status != "complete"
        except stripe.InvalidRequestError:
            # Se pagó o expiró entre las dos llamadas: se vuelve a preguntar.
            try:
                return self._sesiones.retrieve(referencia).status != "complete"
            except stripe.StripeError as exc:
                raise PasarelaNoDisponible("No se pudo cancelar el pago con tarjeta") from exc
        except stripe.StripeError as exc:
            raise PasarelaNoDisponible("No se pudo cancelar el pago con tarjeta") from exc

    def leer_evento(self, cuerpo: bytes, firma: str | None) -> EventoDePago:
        if not firma:
            raise FirmaInvalida("Falta la firma")
        try:
            stripe.WebhookSignature.verify_header(
                cuerpo.decode("utf-8"), firma, self._secreto_webhook, TOLERANCIA_FIRMA_S
            )
            evento = json.loads(cuerpo)
        except (stripe.SignatureVerificationError, UnicodeDecodeError, ValueError) as exc:
            raise FirmaInvalida("Firma inválida") from exc

        tipo = _TIPOS.get(evento.get("type"), "ignorado")
        objeto = (evento.get("data") or {}).get("object") or {}
        if tipo == "ignorado" or objeto.get("object") != "checkout.session":
            return EventoDePago(id=str(evento.get("id")), tipo="ignorado")
        if evento["type"] == "checkout.session.completed" and objeto.get("payment_status") != "paid":
            # Métodos asíncronos: el cobro llega después en async_payment_succeeded.
            return EventoDePago(id=str(evento.get("id")), tipo="ignorado")

        orden_id = (objeto.get("metadata") or {}).get("orden_id")
        total = objeto.get("amount_total")
        return EventoDePago(
            id=str(evento["id"]),
            tipo=tipo,
            referencia=objeto.get("id"),
            orden_id=int(orden_id) if orden_id and str(orden_id).isdigit() else None,
            monto=(Decimal(total) / 100).quantize(Decimal("0.01")) if isinstance(total, int) else None,
            moneda=objeto.get("currency"),
        )
