"""Pagos contra PostgreSQL: tabla de la migración 0003, un solo pago en curso por orden y aviso idempotente."""

from decimal import Decimal

import pytest

from app.checkout import servicio
from app.ports.pagos import PagoRegistro
from app.shared.auth import UsuarioActual
from app.shared.errores import Conflicto
from tests.pasarela_falsa import PasarelaFalsa

DIANA = UsuarioActual(1, "comprador")
URL = "https://facfood.test"


def _aviso(pasarela, ref, **kw):
    s = pasarela.sesiones[ref]
    s["estado"] = "complete" if kw.get("tipo", "pagado") == "pagado" else s["estado"]
    from app.ports.pagos import EventoDePago
    return EventoDePago(kw.get("id", f"evt_{ref}"), kw.get("tipo", "pagado"), ref, s["orden_id"],
                        kw.get("monto", s["monto"]), "mxn")


def test_pago_con_tarjeta_de_punta_a_punta(fabrica_pg):
    pasarela = PasarelaFalsa()
    orden = servicio.crear_orden(fabrica_pg, DIANA, 1, [(1, 2), (3, 1)], "pickup", None)
    servicio.aplicar_cupon(fabrica_pg, DIANA, orden["id"], "BIENVENIDA15")
    sesion = servicio.iniciar_pago(fabrica_pg, pasarela, DIANA, orden["id"], URL)
    assert sesion["monto"] == "65.08"
    ref = pasarela.ultima()

    evento = _aviso(pasarela, ref)
    assert servicio.procesar_evento(fabrica_pg, pasarela, evento) == "pagado"
    assert servicio.procesar_evento(fabrica_pg, pasarela, evento) == "repetido"

    with fabrica_pg() as uow:
        r = uow.ordenes.por_id(orden["id"])
        assert (r.orden.estado.value, r.orden.total) == ("PAGADA", Decimal("65.08"))
        assert uow.cupones.por_codigo("BIENVENIDA15").cupon.usos_actuales == 1
        assert [e.estado for e in uow.eventos.de_orden(orden["id"])] == ["CREADA", "PAGADA"]
        pagos = uow.pagos.de_orden(orden["id"])
        assert [(p.estado, p.referencia, p.monto, p.evento_id) for p in pagos] == [
            ("PAGADO", ref, Decimal("65.08"), f"evt_{ref}")]
        assert uow.facturas.de_orden(orden["id"]) is not None


def test_la_base_impide_dos_pagos_en_curso_para_la_misma_orden(fabrica_pg):
    orden = servicio.crear_orden(fabrica_pg, DIANA, 1, [(1, 1)], "pickup", None)
    with fabrica_pg() as uow:
        uow.pagos.agregar(PagoRegistro(None, orden["id"], "stripe", "cs_a", Decimal("20.88")))
        with pytest.raises(Conflicto) as exc:
            uow.pagos.agregar(PagoRegistro(None, orden["id"], "stripe", "cs_b", Decimal("20.88")))
    assert exc.value.codigo == "PAGO_EN_CURSO"


def test_cancelar_y_expirar_en_postgres(fabrica_pg):
    pasarela = PasarelaFalsa()
    orden = servicio.crear_orden(fabrica_pg, DIANA, 1, [(1, 1)], "pickup", None)
    servicio.iniciar_pago(fabrica_pg, pasarela, DIANA, orden["id"], URL)
    with pytest.raises(Conflicto):
        servicio.aplicar_cupon(fabrica_pg, DIANA, orden["id"], "BIENVENIDA15")
    servicio.cancelar_pago(fabrica_pg, pasarela, DIANA, orden["id"])
    servicio.iniciar_pago(fabrica_pg, pasarela, DIANA, orden["id"], URL)
    assert servicio.procesar_evento(fabrica_pg, pasarela, _aviso(pasarela, pasarela.ultima(), tipo="expirado")) == "expirado"
    with fabrica_pg() as uow:
        assert [p.estado for p in uow.pagos.de_orden(orden["id"])] == ["EXPIRADO", "EXPIRADO"]
        assert uow.pagos.pendiente_de_orden(orden["id"]) is None
