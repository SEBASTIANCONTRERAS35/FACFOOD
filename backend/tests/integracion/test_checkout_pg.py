"""Checkout contra PostgreSQL: el pago bloquea filas de verdad (SELECT ... FOR UPDATE)."""

import threading

import pytest

from app.checkout import servicio
from app.domain.crm.retencion import CuponInvalidoError
from app.shared.auth import UsuarioActual
from app.shared.errores import Conflicto

DIANA = UsuarioActual(1, "comprador")
SEBASTIAN = UsuarioActual(2, "comprador")


def test_flujo_completo_con_postgres(fabrica_pg):
    orden = servicio.crear_orden(fabrica_pg, DIANA, 1, [(1, 2), (3, 1)], "pickup", None)
    orden = servicio.aplicar_cupon(fabrica_pg, DIANA, orden["id"], "BIENVENIDA15")
    pagada = servicio.pagar(fabrica_pg, DIANA, orden["id"], None)
    assert (pagada["estado"], pagada["descuento"], pagada["origen_descuento"], pagada["total"]) == (
        "PAGADA", "9.90", "cupon", "65.08",
    )
    with fabrica_pg() as uow:
        r = uow.ordenes.por_id(orden["id"])
        assert r.orden.origen_descuento == "cupon"  # se guarda en la columna de la migración 0002
        assert uow.cupones.por_codigo("BIENVENIDA15").cupon.usos_actuales == 1
        assert [e.estado for e in uow.eventos.de_orden(orden["id"])] == ["CREADA", "PAGADA"]
    with pytest.raises(Conflicto):
        servicio.pagar(fabrica_pg, DIANA, orden["id"], None)


def test_distancia_de_entrega_con_postgis(fabrica_pg):
    destinos = {d["nombre"]: d["id"] for d in servicio.destinos(fabrica_pg)}
    orden = servicio.crear_orden(fabrica_pg, DIANA, 1, [(1, 1)], "estudiante", destinos["Facultad de Arquitectura"])
    km = float(orden["distancia_km"])
    assert 0.3 < km < 1.0 and orden["envio"] == f"{round(km * 5, 2):.2f}"


def test_dos_pagos_simultaneos_con_un_cupon_de_un_solo_uso(fabrica_pg):
    a = servicio.crear_orden(fabrica_pg, DIANA, 1, [(1, 2)], "pickup", None)
    b = servicio.crear_orden(fabrica_pg, SEBASTIAN, 1, [(1, 10)], "pickup", None)
    servicio.aplicar_cupon(fabrica_pg, DIANA, a["id"], "UNICO20")
    servicio.aplicar_cupon(fabrica_pg, SEBASTIAN, b["id"], "UNICO20")

    resultados, salida = [], threading.Barrier(2)

    def pagar(usuario, orden_id):
        salida.wait()
        try:
            servicio.pagar(fabrica_pg, usuario, orden_id, None)
            resultados.append("pagada")
        except CuponInvalidoError:
            resultados.append("cupon agotado")

    hilos = [threading.Thread(target=pagar, args=(DIANA, a["id"])),
             threading.Thread(target=pagar, args=(SEBASTIAN, b["id"]))]
    [h.start() for h in hilos]
    [h.join() for h in hilos]

    assert sorted(resultados) == ["cupon agotado", "pagada"]
    with fabrica_pg() as uow:
        assert uow.cupones.por_codigo("UNICO20").cupon.usos_actuales == 1
