"""
Prueba unitaria pura de la capa de Dominio.
No depende de base de datos ni frameworks externos.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from domain import Pedido, Pickup, EntregaEstudiante


def test_pickup_no_agrega_costo_extra():
    pedido = Pedido(producto_precio=80)
    metodo = Pickup()

    costo = metodo.calcularCosto(pedido)

    assert costo == 80


def test_entrega_estudiante_agrega_costo_por_distancia():
    pedido = Pedido(producto_precio=80, distancia_km=2)
    metodo = EntregaEstudiante()

    costo = metodo.calcularCosto(pedido)

    assert costo == 90  # 80 + (2 * 5)


def test_ejecutar_entrega_pickup_devuelve_mensaje_correcto():
    pedido = Pedido(producto_precio=50)
    metodo = Pickup()

    resultado = metodo.ejecutarEntrega(pedido)

    assert "recoger" in resultado.lower()