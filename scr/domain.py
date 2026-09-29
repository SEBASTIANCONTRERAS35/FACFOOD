"""
Capa de Dominio - FACFOOD
Patrón de diseño: Strategy (Gang of Four)

Cada método de entrega implementa la interfaz MetodoDeEntrega,
sin depender de base de datos ni frameworks (aislado para pruebas puras).
"""

from abc import ABC, abstractmethod


class Pedido:
    def __init__(self, producto_precio: float, distancia_km: float = 0.0):
        self.producto_precio = producto_precio
        self.distancia_km = distancia_km


class MetodoDeEntrega(ABC):
    @abstractmethod
    def calcularCosto(self, pedido: Pedido) -> float:
        ...

    @abstractmethod
    def ejecutarEntrega(self, pedido: Pedido) -> str:
        ...


class Pickup(MetodoDeEntrega):
    """El usuario recoge su pedido directamente en el punto de venta."""

    def calcularCosto(self, pedido: Pedido) -> float:
        return pedido.producto_precio  # sin costo extra de entrega

    def ejecutarEntrega(self, pedido: Pedido) -> str:
        return "Pedido listo para recoger en el punto de venta"


class EntregaEstudiante(MetodoDeEntrega):
    """Un estudiante lleva el pedido hasta la facultad del comprador."""

    COSTO_POR_KM = 5.0

    def calcularCosto(self, pedido: Pedido) -> float:
        return pedido.producto_precio + (pedido.distancia_km * self.COSTO_POR_KM)

    def ejecutarEntrega(self, pedido: Pedido) -> str:
        return "Pedido en camino con estudiante repartidor"
