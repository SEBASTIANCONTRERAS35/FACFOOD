"""
Pruebas unitarias (TDD) para la entidad Usuario — Sprint 2.
Cubre: Paso 2 (perfil dual comprador/vendedor) y
       Paso 3 (hashing Art.18 LFPDPPP + consentimiento Art.7 LFPDPPP).
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from usuario import Usuario, ConsentimientoRequeridoError, PerfilNoElegibleError


# ---- Paso 1 y 3: consentimiento ----
def test_no_se_puede_registrar_sin_consentimiento():
    with pytest.raises(ConsentimientoRequeridoError):
        Usuario(nombre="Luis", credencial_unam="123456789", consentimiento_datos=False)


def test_usuario_inicia_como_comprador():
    usuario = Usuario(nombre="Luis", credencial_unam="123456789", consentimiento_datos=True)
    assert usuario.rol == "comprador"
    assert usuario.pedidos_completados == 0


# ---- Paso 2: regla core de negocio (perfil dual) ----
def test_no_puede_venderse_con_menos_de_3_pedidos():
    usuario = Usuario(nombre="Luis", credencial_unam="123456789", consentimiento_datos=True)
    usuario.registrar_pedido_completado()
    usuario.registrar_pedido_completado()

    with pytest.raises(PerfilNoElegibleError):
        usuario.convertirse_en_vendedor()

    assert usuario.rol == "comprador"


def test_se_convierte_en_vendedor_tras_3_pedidos():
    usuario = Usuario(nombre="Luis", credencial_unam="123456789", consentimiento_datos=True)
    for _ in range(3):
        usuario.registrar_pedido_completado()

    usuario.convertirse_en_vendedor()

    assert usuario.rol == "vendedor"


# ---- Paso 3: hashing de contraseña (Art. 18 LFPDPPP) ----
def test_password_se_guarda_hasheada_no_en_texto_plano():
    usuario = Usuario(nombre="Luis", credencial_unam="123456789", consentimiento_datos=True)
    usuario.registrar_password("miPasswordSegura123")

    assert usuario.password_hash is not None
    assert b"miPasswordSegura123" not in usuario.password_hash


def test_verificar_password_correcta_devuelve_true():
    usuario = Usuario(nombre="Luis", credencial_unam="123456789", consentimiento_datos=True)
    usuario.registrar_password("miPasswordSegura123")

    assert usuario.verificar_password("miPasswordSegura123") is True


def test_verificar_password_incorrecta_devuelve_false():
    usuario = Usuario(nombre="Luis", credencial_unam="123456789", consentimiento_datos=True)
    usuario.registrar_password("miPasswordSegura123")

    assert usuario.verificar_password("passwordIncorrecta") is False
