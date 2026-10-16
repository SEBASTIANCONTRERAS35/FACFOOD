"""
Capa de Dominio - FACFOOD
Patrón de diseño: Strategy (Gang of Four)

Cada método de entrega implementa la interfaz MetodoDeEntrega,
sin depender de base de datos ni frameworks (aislado para pruebas puras).
La orden del ERP usa la estrategia para calcular su costo de envío.
"""

from abc import ABC, abstractmethod


class Pedido:
    def __init__(self, producto_precio: float, distancia_km: float = 0.0):
        self.producto_precio = producto_precio
        self.distancia_km = distancia_km


class MetodoDeEntrega(ABC):
    nombre: str

    @abstractmethod
    def calcularCostoEnvio(self, distancia_km: float) -> float:
        ...

    def calcularCosto(self, pedido: Pedido) -> float:
        return pedido.producto_precio + self.calcularCostoEnvio(pedido.distancia_km)

    @abstractmethod
    def ejecutarEntrega(self, pedido: Pedido) -> str:
        ...


class Pickup(MetodoDeEntrega):
    """El usuario recoge su pedido directamente en el punto de venta."""

    nombre = "pickup"

    def calcularCostoEnvio(self, distancia_km: float) -> float:
        return 0.0  # sin costo extra de entrega

    def ejecutarEntrega(self, pedido: Pedido) -> str:
        return "Pedido listo para recoger en el punto de venta"


class EntregaEstudiante(MetodoDeEntrega):
    """Un estudiante lleva el pedido hasta la facultad del comprador."""

    nombre = "estudiante"
    COSTO_POR_KM = 5.0

    def calcularCostoEnvio(self, distancia_km: float) -> float:
        if distancia_km < 0:
            raise ValueError("La distancia no puede ser negativa")
        return round(distancia_km * self.COSTO_POR_KM, 2)

    def ejecutarEntrega(self, pedido: Pedido) -> str:
        return "Pedido en camino con estudiante repartidor"


METODOS = {m.nombre: m for m in (Pickup, EntregaEstudiante)}


def metodo_de_entrega(nombre: str) -> MetodoDeEntrega:
    """Devuelve la estrategia por su nombre ("pickup" o "estudiante")."""
    try:
        return METODOS[nombre]()
    except KeyError:
        raise ValueError(f"Método de entrega desconocido: {nombre!r}")
