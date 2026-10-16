"""
Pruebas unitarias del módulo CRM (cupones y lealtad).
Aisladas: no dependen de base de datos ni de frameworks.
"""

from datetime import date, timedelta

import pytest


from app.domain.crm.retencion import (
    Cupon,
    CuponInvalidoError,
    nivel_lealtad,
    descuento_lealtad,
    mejor_descuento,
    cupon_bienvenida,
)

HOY = date(2026, 10, 12)


def test_cupon_aplica_su_porcentaje():
    cupon = Cupon("PROMO15", porcentaje=15, vigente_hasta=HOY + timedelta(days=5))
    assert cupon.calcular_descuento(100, HOY) == 15


def test_cupon_respeta_el_tope_de_descuento():
    cupon = Cupon("PROMO15", 15, HOY + timedelta(days=5), tope_descuento=30)
    assert cupon.calcular_descuento(400, HOY) == 30  # 15% serian 60


def test_cupon_vencido_lanza_error():
    cupon = Cupon("VIEJO", 10, HOY - timedelta(days=1))
    with pytest.raises(CuponInvalidoError):
        cupon.calcular_descuento(100, HOY)


def test_cupon_no_aplica_si_no_llega_al_pedido_minimo():
    cupon = Cupon("MIN100", 10, HOY + timedelta(days=5), pedido_minimo=100)
    with pytest.raises(CuponInvalidoError):
        cupon.calcular_descuento(80, HOY)


def test_cupon_agotado_tras_sus_usos_maximos():
    cupon = Cupon("UNICO", 10, HOY + timedelta(days=5), usos_maximos=1)
    cupon.registrar_uso()
    with pytest.raises(CuponInvalidoError):
        cupon.calcular_descuento(100, HOY)


def test_niveles_de_lealtad_segun_pedidos_completados():
    assert nivel_lealtad(0) == "bronce"
    assert nivel_lealtad(3) == "plata"
    assert nivel_lealtad(10) == "oro"


def test_descuento_de_lealtad_por_nivel():
    assert descuento_lealtad(200, 0) == 0
    assert descuento_lealtad(200, 3) == 10   # plata 5%
    assert descuento_lealtad(200, 10) == 20  # oro 10%


def test_descuentos_no_se_acumulan_se_aplica_el_mayor():
    cupon = Cupon("PROMO15", 15, HOY + timedelta(days=5))
    # plata (5% = 5) vs cupon (15% = 15) -> gana el cupon
    assert mejor_descuento(100, 3, HOY, cupon) == 15
    # oro (10% = 20) vs cupon (5% = 10) -> gana la lealtad
    cupon_chico = Cupon("PROMO5", 5, HOY + timedelta(days=5))
    assert mejor_descuento(200, 10, HOY, cupon_chico) == 20


def test_cupon_de_bienvenida_solo_para_primer_pedido():
    assert cupon_bienvenida(0, HOY) is not None
    assert cupon_bienvenida(1, HOY) is None
