"""Errores encontrados en la revisión del ERP (2026-10-15), cada uno con su prueba."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.domain.crm.retencion import Cupon, CuponInvalidoError
from app.domain.entrega import EntregaEstudiante, Pickup
from app.domain.erp.orden import Orden

HOY = date(2026, 10, 16)
CATALOGO = {"taco": Decimal("25.00"), "agua": Decimal("15.50")}


def orden(*lineas):
    o = Orden(CATALOGO, HOY)
    for producto, cantidad in lineas:
        o.agregar_linea(producto, cantidad)
    return o


# ---- 1. La lealtad del CRM se ignoraba ----
def test_cliente_oro_recibe_su_descuento_aunque_el_cupon_sea_menor():
    o = orden(("taco", 8))  # subtotal 200
    o.definir_lealtad(10)  # oro: 10% = 20
    o.aplicar_cupon(Cupon("P5", 5, HOY + timedelta(days=5)))  # 5% = 10
    assert o.descuentos == Decimal("20.00")
    assert o.origen_descuento == "lealtad"


def test_gana_el_cupon_cuando_es_mayor_que_la_lealtad():
    o = orden(("taco", 4))  # 100
    o.definir_lealtad(3)  # plata 5% = 5
    o.aplicar_cupon(Cupon("P15", 15, HOY + timedelta(days=5)))  # 15
    assert o.descuentos == Decimal("15.00") and o.origen_descuento == "cupon"


def test_si_gana_la_lealtad_el_cupon_no_se_consume():
    c = Cupon("P5", 5, HOY + timedelta(days=5))
    o = orden(("taco", 8))
    o.definir_lealtad(10)
    o.aplicar_cupon(c)
    o.avanzar_estado("PAGADA")
    assert c.usos_actuales == 0


def test_sin_cupon_ni_lealtad_no_hay_descuento():
    o = orden(("taco", 1))
    assert o.descuentos == Decimal("0.00") and o.origen_descuento is None


# ---- 2. Un cupón que deja de ser válido bloqueaba la orden ----
def test_cupon_agotado_se_puede_quitar_para_poder_pagar():
    c = Cupon("UNO", 10, HOY + timedelta(days=5), usos_maximos=1)
    o = orden(("taco", 4))
    o.aplicar_cupon(c)
    c.registrar_uso()  # alguien más lo usó antes de que pagáramos
    with pytest.raises(CuponInvalidoError):
        o.avanzar_estado("PAGADA")
    o.quitar_cupon()
    o.avanzar_estado("PAGADA")
    assert o.descuentos == Decimal("0.00")


def test_editar_la_orden_con_un_cupon_que_ya_no_es_valido_no_truena():
    c = Cupon("UNO", 10, HOY + timedelta(days=5), usos_maximos=1)
    o = orden(("taco", 4))
    o.aplicar_cupon(c)
    c.registrar_uso()
    o.agregar_linea("agua", 1)  # antes lanzaba CuponInvalidoError y dejaba la línea a medias
    assert len(o.lineas) == 2 and o.descuentos == Decimal("0.00")


# ---- 3. Un cupón con pedido mínimo quedaba guardado aunque fallara ----
def test_cupon_que_no_llega_al_minimo_no_se_guarda():
    o = orden(("taco", 1))  # 25 < 100
    with pytest.raises(CuponInvalidoError):
        o.aplicar_cupon(Cupon("MIN100", 10, HOY + timedelta(days=5), pedido_minimo=100))
    assert o.cupon is None
    o.agregar_linea("taco", 1)  # ya no lanza error
    assert o.subtotal == Decimal("50.00")


# ---- 4. Se aceptaban cantidades decimales y después fallaba el subtotal ----
@pytest.mark.parametrize("cantidad", [1.5, True, "2"])
def test_la_cantidad_debe_ser_un_entero(cantidad):
    o = Orden(CATALOGO, HOY)
    with pytest.raises(ValueError):
        o.agregar_linea("taco", cantidad)
    assert o.lineas == ()


# ---- Integración con el Strategy de entrega ----
def test_el_envio_lo_calcula_la_estrategia():
    o = orden(("taco", 1))
    o.definir_entrega(EntregaEstudiante(), Decimal("0.6"))
    assert o.envio == Decimal("3.00") and o.metodo_entrega == "estudiante"
    o.definir_entrega(Pickup())
    assert o.envio == Decimal("0.00") and o.metodo_entrega == "pickup"


def test_caso_de_la_pantalla_04():
    """2 tacos de pastor ($18) + 1 quesadilla ($30), cupón de bienvenida 15% (tope $30)."""
    o = Orden({"pastor": Decimal("18.00"), "quesadilla": Decimal("30.00")}, HOY)
    o.agregar_linea("pastor", 2)
    o.agregar_linea("quesadilla", 1)
    o.definir_lealtad(0)
    o.aplicar_cupon(Cupon("BIENVENIDA15", 15, HOY + timedelta(days=30), tope_descuento=30))
    o.definir_entrega(Pickup())
    assert (o.subtotal, o.descuentos, o.iva, o.envio, o.total) == (
        Decimal("66.00"), Decimal("9.90"), Decimal("8.98"), Decimal("0.00"), Decimal("65.08"),
    )


def test_restaurar_conserva_el_origen_del_descuento():
    o = Orden.restaurar(CATALOGO, HOY, "PAGADA", [], Decimal("5"), Decimal("0"), origen_descuento="lealtad")
    assert o.origen_descuento == "lealtad"
    sin = Orden.restaurar(CATALOGO, HOY, "PAGADA", [], Decimal("0"), Decimal("0"), origen_descuento="cupon")
    assert sin.origen_descuento is None
