"""
Pruebas unitarias (TDD) del módulo ERP: total, estados, factura y pago dividido.
Aisladas: no dependen de base de datos ni de frameworks.
En el módulo financiero, lo que no está cubierto por una prueba se asume roto.
"""

import sys
import os
from datetime import date, timedelta
from decimal import Decimal

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from crm.retencion import Cupon, CuponInvalidoError
from erp.orden import (
    Orden,
    EstadoOrden,
    InvalidStateTransitionException,
    OrdenInmutableError,
    OrdenVaciaError,
    ProductoNoEncontradoError,
    FacturaNoPermitidaError,
    OrdenNoPagadaError,
)
from erp.factura import RfcInvalidoError

HOY = date(2026, 10, 13)
CATALOGO = {"torta": Decimal("100.00"), "agua": Decimal("20.00")}


def nueva_orden():
    return Orden(CATALOGO, fecha=HOY)


def orden_con_torta():
    orden = nueva_orden()
    orden.agregar_linea("torta", 1)
    return orden


def cupon(porcentaje=20, usos=1):
    return Cupon("PROMO", porcentaje, HOY + timedelta(days=5), usos_maximos=usos)


# ---- Total: (Subtotal - Descuentos) + IVA(16%) + Envío ----
def test_calcular_total_orden_con_iva_y_descuento():
    orden = orden_con_torta()
    orden.aplicar_cupon(cupon(20))
    assert orden.total == Decimal("92.80")  # 100 - 20% + 16% IVA


def test_total_sin_descuento_incluye_iva():
    assert orden_con_torta().total == Decimal("116.00")


def test_envio_se_suma_al_final_sin_iva():
    orden = orden_con_torta()
    orden.definir_envio(Decimal("25"))
    assert orden.total == Decimal("141.00")  # 100 + 16 IVA + 25 envío


def test_subtotal_suma_precio_por_cantidad():
    orden = nueva_orden()
    orden.agregar_linea("torta", 2)
    orden.agregar_linea("agua", 3)
    assert orden.subtotal == Decimal("260.00")


# ---- Nunca confiar en el frontend ----
def test_el_precio_lo_dicta_el_servidor_no_el_cliente():
    orden = nueva_orden()
    with pytest.raises(TypeError):
        orden.agregar_linea("torta", 1, precio_unitario=Decimal("5.00"))
    orden.agregar_linea("torta", 1)
    assert orden.lineas[0].precio_unitario == Decimal("100.00")


def test_producto_inexistente_lanza_error():
    with pytest.raises(ProductoNoEncontradoError):
        nueva_orden().agregar_linea("pizza", 1)


# ---- Máquina de estados ----
def test_transicion_estado_invalida_lanza_excepcion():
    orden = orden_con_torta()
    with pytest.raises(InvalidStateTransitionException):
        orden.avanzar_estado("ENTREGADA")  # CREADA -> ENTREGADA está prohibido


def test_secuencia_completa_de_estados():
    orden = orden_con_torta()
    for estado in ["PAGADA", "EN_PREPARACION", "ENVIADA", "ENTREGADA"]:
        orden.avanzar_estado(estado)
    assert orden.estado is EstadoOrden.ENTREGADA


def test_no_se_puede_regresar_a_un_estado_anterior():
    orden = orden_con_torta()
    orden.avanzar_estado("PAGADA")
    with pytest.raises(InvalidStateTransitionException):
        orden.avanzar_estado("CREADA")


def test_solo_se_cancela_desde_creada():
    cancelable = orden_con_torta()
    cancelable.avanzar_estado("CANCELADA")
    assert cancelable.estado is EstadoOrden.CANCELADA

    pagada = orden_con_torta()
    pagada.avanzar_estado("PAGADA")
    with pytest.raises(InvalidStateTransitionException):
        pagada.avanzar_estado("CANCELADA")


def test_estado_desconocido_lanza_excepcion():
    with pytest.raises(InvalidStateTransitionException):
        orden_con_torta().avanzar_estado("VOLANDO")


def test_no_se_puede_pagar_una_orden_vacia():
    with pytest.raises(OrdenVaciaError):
        nueva_orden().avanzar_estado("PAGADA")


def test_orden_pagada_es_inmutable():
    orden = orden_con_torta()
    orden.avanzar_estado("PAGADA")
    with pytest.raises(OrdenInmutableError):
        orden.agregar_linea("agua", 1)


# ---- Cupones (integración con el CRM) ----
def test_el_cupon_se_consume_solo_al_pagar():
    c = cupon(20)
    orden = orden_con_torta()
    orden.aplicar_cupon(c)
    assert c.usos_actuales == 0
    orden.avanzar_estado("PAGADA")
    assert c.usos_actuales == 1


def test_cupon_agotado_bloquea_el_pago():
    c = cupon(20, usos=1)
    primera = orden_con_torta()
    segunda = orden_con_torta()
    primera.aplicar_cupon(c)
    segunda.aplicar_cupon(c)
    primera.avanzar_estado("PAGADA")
    with pytest.raises(CuponInvalidoError):
        segunda.avanzar_estado("PAGADA")


# ---- Factura ----
def test_factura_solo_se_genera_en_estado_pagada():
    orden = orden_con_torta()
    with pytest.raises(FacturaNoPermitidaError):
        orden.generar_factura("XAXX010101000")  # aún CREADA

    orden.avanzar_estado("PAGADA")
    factura = orden.generar_factura("XAXX010101000")
    assert factura.rfc_receptor == "XAXX010101000"

    orden.avanzar_estado("EN_PREPARACION")
    with pytest.raises(FacturaNoPermitidaError):
        orden.generar_factura("XAXX010101000")


def test_factura_trae_folio_y_xml_con_el_total():
    orden = orden_con_torta()
    orden.avanzar_estado("PAGADA")
    factura = orden.generar_factura("XAXX010101000")
    assert factura.folio_fiscal is not None
    assert b"XAXX010101000" in factura.xml_data
    assert b'Total="116.00"' in factura.xml_data


def test_rfc_invalido_lanza_error():
    orden = orden_con_torta()
    orden.avanzar_estado("PAGADA")
    with pytest.raises(RfcInvalidoError):
        orden.generar_factura("RFC-MALO")


# ---- Marketplace: pago dividido ----
def test_dividir_pago_entre_plataforma_y_vendedor():
    orden = orden_con_torta()
    orden.aplicar_cupon(cupon(20))  # base = 100 - 20 = 80 (el vendedor absorbe el descuento)
    orden.avanzar_estado("PAGADA")
    pago = orden.dividir_pago(comision_pct=Decimal("10"))
    assert pago.comision_plataforma == Decimal("8.00")
    assert pago.neto_vendedor == Decimal("72.00")


def test_dividir_pago_requiere_orden_pagada():
    with pytest.raises(OrdenNoPagadaError):
        orden_con_torta().dividir_pago(comision_pct=Decimal("10"))
