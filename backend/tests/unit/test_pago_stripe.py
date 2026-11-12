"""Adaptador de Stripe sin red: firma real (HMAC-SHA256) generada aquí y cliente falso."""

import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
import stripe

from app.adapters.pagos.stripe_checkout import PagoStripe, a_centavos
from app.ports.pagos import FirmaInvalida, PasarelaNoDisponible
from app.shared import pasarela as modulo_pasarela

SECRETO = "whsec_prueba_local"


def firmar(cuerpo: bytes, secreto=SECRETO, t=None) -> str:
    t = int(time.time()) if t is None else t
    v1 = hmac.new(secreto.encode(), f"{t}.".encode() + cuerpo, hashlib.sha256).hexdigest()
    return f"t={t},v1={v1}"


def evento(tipo="checkout.session.completed", **sesion) -> bytes:
    objeto = {"id": "cs_test_1", "object": "checkout.session", "payment_status": "paid",
              "amount_total": 6508, "currency": "mxn", "metadata": {"orden_id": "7", "pago_id": "3"}}
    objeto.update(sesion)
    return json.dumps({"id": "evt_1", "type": tipo, "data": {"object": objeto}}).encode()


class SesionesFalsas:
    def __init__(self, estado="open"):
        self.estado, self.creadas, self.expiradas = estado, [], []

    def create(self, params, options):
        self.creadas.append((params, options))
        return SimpleNamespace(id="cs_test_1", url="https://checkout.stripe.com/c/pay/cs_test_1")

    def retrieve(self, ref):
        return SimpleNamespace(status=self.estado)

    def expire(self, ref):
        self.expiradas.append(ref)
        self.estado = "expired"
        return SimpleNamespace(status="expired")


def pasarela(sesiones=None) -> PagoStripe:
    cliente = SimpleNamespace(v1=SimpleNamespace(checkout=SimpleNamespace(sessions=sesiones or SesionesFalsas())))
    return PagoStripe("sk_test_x", SECRETO, cliente=cliente)


# ---- Firma del webhook ----
def test_un_aviso_con_firma_valida_se_traduce():
    cuerpo = evento()
    e = pasarela().leer_evento(cuerpo, firmar(cuerpo))
    assert (e.id, e.tipo, e.referencia, e.orden_id, e.monto, e.moneda) == (
        "evt_1", "pagado", "cs_test_1", 7, Decimal("65.08"), "mxn")


@pytest.mark.parametrize("firma", [
    None, "", "basura", firmar(b"otro cuerpo"), firmar(evento(), secreto="whsec_otro"),
    firmar(evento(), t=int(time.time()) - 600),  # repetición de un aviso viejo
])
def test_sin_firma_valida_se_rechaza(firma):
    with pytest.raises(FirmaInvalida):
        pasarela().leer_evento(evento(), firma)


def test_un_cuerpo_alterado_despues_de_firmar_se_rechaza():
    original = evento()
    alterado = evento(amount_total=1)
    with pytest.raises(FirmaInvalida):
        pasarela().leer_evento(alterado, firmar(original))


@pytest.mark.parametrize("tipo,esperado", [
    ("checkout.session.expired", "expirado"),
    ("checkout.session.async_payment_failed", "fallido"),
    ("checkout.session.async_payment_succeeded", "pagado"),
    ("payment_intent.succeeded", "ignorado"),
])
def test_tipos_de_aviso(tipo, esperado):
    cuerpo = evento(tipo)
    assert pasarela().leer_evento(cuerpo, firmar(cuerpo)).tipo == esperado


def test_una_sesion_completada_sin_cobrar_aun_se_ignora():
    cuerpo = evento(payment_status="unpaid")
    assert pasarela().leer_evento(cuerpo, firmar(cuerpo)).tipo == "ignorado"


# ---- Sesión de Checkout ----
def test_la_sesion_se_crea_en_centavos_mxn_con_metadatos_y_llave_de_idempotencia():
    sesiones = SesionesFalsas()
    expira = datetime(2026, 11, 12, 18, 30, tzinfo=timezone.utc)
    s = pasarela(sesiones).crear_sesion(
        pago_id=3, orden_id=7, monto=Decimal("65.08"), descripcion="FACFOOD · Pedido #7", correo="d@unam.mx",
        url_exito="https://facfood.vercel.app/pedido/7/pago?resultado=exito",
        url_cancelar="https://facfood.vercel.app/pedido/7/pago?resultado=cancelado", expira_en=expira,
    )
    assert s.referencia == "cs_test_1" and s.url.startswith("https://checkout.stripe.com/")
    params, options = sesiones.creadas[0]
    precio = params["line_items"][0]["price_data"]
    assert (precio["currency"], precio["unit_amount"]) == ("mxn", 6508)
    assert params["metadata"] == {"orden_id": "7", "pago_id": "3"} and params["client_reference_id"] == "3"
    assert params["expires_at"] == int(expira.timestamp()) and params["payment_method_types"] == ["card"]
    assert options == {"idempotency_key": "facfood-pago-3"}


def test_si_stripe_falla_se_reporta_sin_detalles():
    class Falla(SesionesFalsas):
        def create(self, params, options):
            raise stripe.APIConnectionError("sin red")
    with pytest.raises(PasarelaNoDisponible):
        pasarela(Falla()).crear_sesion(pago_id=1, orden_id=1, monto=Decimal("10"), descripcion="x", correo=None,
                                      url_exito="u", url_cancelar="u", expira_en=datetime.now(timezone.utc) + timedelta(minutes=31))


def test_cancelar_expira_una_sesion_abierta_y_no_una_pagada():
    abierta = SesionesFalsas("open")
    assert pasarela(abierta).cancelar_sesion("cs_test_1") is True and abierta.expiradas == ["cs_test_1"]
    pagada = SesionesFalsas("complete")
    assert pasarela(pagada).cancelar_sesion("cs_test_1") is False and pagada.expiradas == []


def test_centavos_exactos():
    assert [a_centavos(Decimal(m)) for m in ("65.08", "0.10", "100.00")] == [6508, 10, 10000]


# ---- Configuración: falla cerrada ----
def test_sin_secretos_stripe_no_arranca():
    modulo_pasarela._pasarela.cache_clear()
    with pytest.raises(ValueError):
        modulo_pasarela._pasarela("stripe", "sk_test_x", None)
    with pytest.raises(ValueError):
        modulo_pasarela._pasarela("tarjeta", None, None)
    assert modulo_pasarela._pasarela("simulado", None, None).nombre == "simulado"
