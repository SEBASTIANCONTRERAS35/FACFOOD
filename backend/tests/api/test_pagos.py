"""Pagos (ADR 004): checkout con pasarela, webhook firmado e idempotente, y pago simulado."""

from decimal import Decimal

import pytest

from app.shared.pasarela import obtener_pasarela
from tests.api.test_checkout import DIANA, SEBASTIAN, crear
from tests.conftest import como
from tests.pasarela_falsa import FIRMA_VALIDA, PasarelaFalsa


@pytest.fixture
def pasarela(cliente):
    p = PasarelaFalsa()
    cliente.app.dependency_overrides[obtener_pasarela] = lambda: p
    return p


def avisar(cliente, cuerpo: bytes, firma=FIRMA_VALIDA):
    return cliente.post("/pagos/webhook", content=cuerpo, headers={"Stripe-Signature": firma} if firma else {})


def checkout(cliente, orden_id, usuario=DIANA):
    return cliente.post(f"/ordenes/{orden_id}/checkout", headers=como(usuario))


def orden(cliente, orden_id, usuario=DIANA):
    return cliente.get(f"/ordenes/{orden_id}", headers=como(usuario)).json()


# ---- Pasarela simulada (por defecto) ----
def test_con_el_simulado_el_checkout_no_redirige_y_se_paga_con_pagar(cliente, fabrica):
    o = crear(cliente).json()
    r = checkout(cliente, o["id"])
    assert r.status_code == 200
    assert r.json() == {"pasarela": "simulado", "orden_id": o["id"], "url": None, "monto": o["total"],
                        "expira_en": None}

    pagada = cliente.post(f"/ordenes/{o['id']}/pagar", headers=como(DIANA)).json()
    assert pagada["estado"] == "PAGADA"
    with fabrica() as uow:
        pagos = uow.pagos.de_orden(o["id"])
    assert [(p.proveedor, p.estado, p.monto) for p in pagos] == [("simulado", "PAGADO", Decimal(o["total"]))]


def test_con_el_simulado_el_webhook_rechaza_todo(cliente):
    r = avisar(cliente, b'{"id":"evt_1"}')
    assert r.status_code == 400 and r.json()["codigo"] == "FIRMA_INVALIDA"


# ---- Pasarela con redirección (Stripe) ----
def test_flujo_completo_con_tarjeta(cliente, fabrica, pasarela):
    o = crear(cliente).json()
    cliente.post(f"/ordenes/{o['id']}/cupon", headers=como(DIANA), json={"codigo": "BIENVENIDA15"})

    s = checkout(cliente, o["id"]).json()
    ref = pasarela.ultima()
    assert s["pasarela"] == "stripe" and s["url"] == f"https://checkout.stripe.test/{ref}"
    assert s["monto"] == "65.08" and pasarela.sesiones[ref]["monto"] == Decimal("65.08")
    assert pasarela.sesiones[ref]["url_exito"].endswith(f"/pedido/{o['id']}/pago?resultado=exito")
    assert orden(cliente, o["id"])["estado"] == "CREADA"  # regresar del navegador no paga nada

    assert avisar(cliente, pasarela.aviso(ref)).json() == {"recibido": True}

    pagada = orden(cliente, o["id"])
    assert (pagada["estado"], pagada["total"]) == ("PAGADA", "65.08") and pagada["factura_folio"]
    with fabrica() as uow:
        assert [e.estado for e in uow.eventos.de_orden(o["id"])] == ["CREADA", "PAGADA"]
        assert uow.cupones.por_codigo("BIENVENIDA15").cupon.usos_actuales == 1
        assert [(p.estado, p.referencia) for p in uow.pagos.de_orden(o["id"])] == [("PAGADO", ref)]


def test_el_mismo_aviso_dos_veces_no_paga_dos_veces(cliente, fabrica, pasarela):
    o = crear(cliente).json()
    cliente.post(f"/ordenes/{o['id']}/cupon", headers=como(DIANA), json={"codigo": "BIENVENIDA15"})
    checkout(cliente, o["id"])
    aviso = pasarela.aviso(pasarela.ultima())
    assert avisar(cliente, aviso).status_code == 200
    assert avisar(cliente, aviso).status_code == 200
    with fabrica() as uow:
        assert [e.estado for e in uow.eventos.de_orden(o["id"])] == ["CREADA", "PAGADA"]
        assert uow.cupones.por_codigo("BIENVENIDA15").cupon.usos_actuales == 1


def test_sin_firma_o_con_firma_alterada_no_se_toca_nada(cliente, pasarela):
    o = crear(cliente).json()
    checkout(cliente, o["id"])
    aviso = pasarela.aviso(pasarela.ultima())
    for firma in (None, "t=1,v1=falsa"):
        r = avisar(cliente, aviso, firma)
        assert r.status_code == 400 and r.json()["codigo"] == "FIRMA_INVALIDA"
        assert "v1=falsa" not in r.text  # no se repite lo que mandó el cliente
    assert orden(cliente, o["id"])["estado"] == "CREADA"


@pytest.mark.parametrize("cambio", [{"monto": "0.01"}, {"moneda": "usd"}, {"orden_id": 999}])
def test_un_aviso_que_no_coincide_con_el_pago_no_confirma(cliente, fabrica, pasarela, cambio):
    o = crear(cliente).json()
    checkout(cliente, o["id"])
    assert avisar(cliente, pasarela.aviso(pasarela.ultima(), **cambio)).status_code == 200
    assert orden(cliente, o["id"])["estado"] == "CREADA"
    with fabrica() as uow:
        assert uow.pagos.pendiente_de_orden(o["id"]) is not None


def test_un_aviso_de_una_sesion_desconocida_se_ignora(cliente, pasarela):
    o = crear(cliente).json()
    checkout(cliente, o["id"])
    pasarela.sesiones["cs_test_ajena"] = {"orden_id": o["id"], "monto": Decimal(o["total"]), "estado": "open"}
    assert avisar(cliente, pasarela.aviso("cs_test_ajena")).status_code == 200
    assert orden(cliente, o["id"])["estado"] == "CREADA"


def test_con_tarjeta_el_pago_simulado_queda_desactivado(cliente, pasarela):
    o = crear(cliente).json()
    r = cliente.post(f"/ordenes/{o['id']}/pagar", headers=como(DIANA))
    assert r.status_code == 409 and r.json()["codigo"] == "PAGO_EN_LINEA_REQUERIDO"
    assert orden(cliente, o["id"])["estado"] == "CREADA"


def test_con_un_pago_en_curso_no_se_edita_y_repetir_devuelve_la_misma_sesion(cliente, pasarela):
    o = crear(cliente).json()
    primera = checkout(cliente, o["id"]).json()
    assert checkout(cliente, o["id"]).json()["url"] == primera["url"]
    assert len(pasarela.sesiones) == 1

    for r in (
        cliente.post(f"/ordenes/{o['id']}/cupon", headers=como(DIANA), json={"codigo": "BIENVENIDA15"}),
        cliente.delete(f"/ordenes/{o['id']}/cupon", headers=como(DIANA)),
        cliente.patch(f"/ordenes/{o['id']}/entrega", headers=como(DIANA), json={"metodo_entrega": "pickup"}),
    ):
        assert r.status_code == 409 and r.json()["codigo"] == "PAGO_EN_CURSO"


def test_cancelar_el_pago_permite_editar_y_abrir_otro(cliente, fabrica, pasarela):
    o = crear(cliente).json()
    checkout(cliente, o["id"])
    primera = pasarela.ultima()
    r = cliente.delete(f"/ordenes/{o['id']}/checkout", headers=como(DIANA))
    assert r.status_code == 200 and r.json()["estado"] == "CREADA"
    assert pasarela.sesiones[primera]["estado"] == "expired"

    con_cupon = cliente.post(f"/ordenes/{o['id']}/cupon", headers=como(DIANA), json={"codigo": "BIENVENIDA15"})
    assert con_cupon.status_code == 200
    nueva = checkout(cliente, o["id"]).json()
    assert pasarela.ultima() != primera and nueva["monto"] == con_cupon.json()["total"]
    with fabrica() as uow:
        assert [p.estado for p in uow.pagos.de_orden(o["id"])] == ["EXPIRADO", "PENDIENTE"]


def test_no_se_cancela_un_pago_que_ya_se_cobro(cliente, pasarela):
    o = crear(cliente).json()
    checkout(cliente, o["id"])
    pasarela.sesiones[pasarela.ultima()]["estado"] = "complete"  # pagó, el aviso aún no llega
    r = cliente.delete(f"/ordenes/{o['id']}/checkout", headers=como(DIANA))
    assert r.status_code == 409 and r.json()["codigo"] == "PAGO_YA_REALIZADO"


def test_una_sesion_expirada_libera_la_orden(cliente, fabrica, pasarela):
    o = crear(cliente).json()
    checkout(cliente, o["id"])
    assert avisar(cliente, pasarela.aviso(pasarela.ultima(), tipo="expirado")).status_code == 200
    with fabrica() as uow:
        assert [p.estado for p in uow.pagos.de_orden(o["id"])] == ["EXPIRADO"]
    r = cliente.post(f"/ordenes/{o['id']}/cupon", headers=como(DIANA), json={"codigo": "BIENVENIDA15"})
    assert r.status_code == 200


def test_si_el_cupon_se_agota_mientras_paga_se_respeta_lo_cobrado(cliente, fabrica, pasarela):
    o = crear(cliente).json()
    cliente.post(f"/ordenes/{o['id']}/cupon", headers=como(DIANA), json={"codigo": "BIENVENIDA15"})
    checkout(cliente, o["id"])
    with fabrica() as uow:  # otro comprador se lleva el último uso mientras Diana paga
        reg = uow.cupones.por_codigo("BIENVENIDA15")
        reg.cupon.usos_actuales = reg.cupon.usos_maximos
        uow.cupones.guardar(reg)
        uow.commit()

    avisar(cliente, pasarela.aviso(pasarela.ultima()))
    pagada = orden(cliente, o["id"])
    assert (pagada["estado"], pagada["total"], pagada["origen_descuento"]) == ("PAGADA", "65.08", "cupon")
    with fabrica() as uow:
        reg = uow.cupones.por_codigo("BIENVENIDA15")
        assert reg.cupon.usos_actuales == reg.cupon.usos_maximos  # no se pasa del límite
        assert uow.cupones.usos_de_usuario(reg.id, DIANA) == 1  # pero sí queda registrado su uso


def test_el_checkout_revalida_el_cupon(cliente, fabrica, pasarela):
    o = crear(cliente).json()
    cliente.post(f"/ordenes/{o['id']}/cupon", headers=como(DIANA), json={"codigo": "BIENVENIDA15"})
    with fabrica() as uow:
        reg = uow.cupones.por_codigo("BIENVENIDA15")
        reg.cupon.usos_actuales = reg.cupon.usos_maximos
        uow.cupones.guardar(reg)
        uow.commit()
    r = checkout(cliente, o["id"])
    assert r.status_code == 422 and r.json()["codigo"] == "CUPON_INVALIDO"
    assert pasarela.sesiones == {}


def test_si_la_pasarela_falla_no_queda_un_pago_colgado(cliente, fabrica, pasarela):
    o = crear(cliente).json()
    pasarela.falla = True
    r = checkout(cliente, o["id"])
    assert r.status_code == 502 and r.json()["codigo"] == "PASARELA_NO_DISPONIBLE"
    with fabrica() as uow:
        assert uow.pagos.de_orden(o["id"]) == []
    pasarela.falla = False
    assert checkout(cliente, o["id"]).status_code == 200


def test_no_se_puede_pagar_la_orden_de_otro(cliente, pasarela):
    o = crear(cliente).json()
    assert checkout(cliente, o["id"], usuario=SEBASTIAN).status_code == 404
    assert cliente.delete(f"/ordenes/{o['id']}/checkout", headers=como(SEBASTIAN)).status_code == 404
    assert pasarela.sesiones == {}


def test_una_orden_pagada_no_abre_otro_cobro(cliente, pasarela):
    o = crear(cliente).json()
    checkout(cliente, o["id"])
    avisar(cliente, pasarela.aviso(pasarela.ultima()))
    r = checkout(cliente, o["id"])
    assert r.status_code == 409 and r.json()["codigo"] == "ORDEN_YA_PAGADA"


def test_el_checkout_requiere_sesion(cliente, pasarela):
    o = crear(cliente).json()
    assert cliente.post(f"/ordenes/{o['id']}/checkout").status_code == 401


def test_el_rfc_viaja_con_el_pago_y_se_valida_antes_de_cobrar(cliente, fabrica, pasarela):
    o = crear(cliente).json()
    r = cliente.post(f"/ordenes/{o['id']}/checkout", headers=como(DIANA), json={"rfc": "MAL"})
    assert r.status_code == 422 and r.json()["codigo"] == "RFC_INVALIDO" and "MAL" not in r.json()["detail"]
    assert pasarela.sesiones == {}

    cliente.post(f"/ordenes/{o['id']}/checkout", headers=como(DIANA), json={"rfc": "romd010203ab1"})
    avisar(cliente, pasarela.aviso(pasarela.ultima()))
    with fabrica() as uow:
        assert uow.facturas.de_orden(o["id"]).factura.rfc_receptor == "ROMD010203AB1"


def test_salud_dice_que_pasarela_esta_activa(cliente):
    assert cliente.get("/salud").json()["pasarela"] == "simulado"
