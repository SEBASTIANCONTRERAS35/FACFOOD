from enum import Enum
from datetime import datetime
import pytest

# Excepción personalizada
class InvalidStateTransitionException(Exception):
    pass

# Enum para los estados de la máquina de estados
class EstadoOrden(Enum):
    CREADA = 1
    PAGADA = 2
    EN_PREPARACION = 3
    ENVIADA = 4
    ENTREGADA = 5
    CANCELADA = 6

class LineaPedido:
    def __init__(self, producto_id, cantidad, precio_unitario):
        self.producto_id = producto_id
        self.cantidad = cantidad
        self.precio_unitario = precio_unitario
        self.subtotal = cantidad * precio_unitario

class Factura:
    def __init__(self, folio_fiscal, rfc_receptor, xml_data):
        self.folio_fiscal = folio_fiscal
        self.rfc_receptor = rfc_receptor
        self.xml_data = xml_data

class Orden:
    def __init__(self):
        self.status = EstadoOrden.CREADA
        self.fecha = datetime.now()
        self.lineas = []
        self.descuento = 0
        self.envio = 0
        self.factura = None

    def agregarLinea(self, linea: LineaPedido):
        self.lineas.append(linea)

    def aplicarCupon(self, descuento):
        self.descuento = descuento

    @property
    def total(self):
        # Álgebra de la orden: (Subtotal - Descuentos) + IVA(16%) + Envío
        subtotal = sum(linea.subtotal for linea in self.lineas)
        total_descuento = subtotal - self.descuento
        iva = total_descuento * 0.16
        return total_descuento + iva + self.envio

    def avanzarEstado(self, nuevo_estado: str):
        # Regla de la Capa de Dominio: Secuencia estricta e irreversible
        transiciones_validas = {
            EstadoOrden.CREADA: [EstadoOrden.PAGADA, EstadoOrden.CANCELADA],
            EstadoOrden.PAGADA: [EstadoOrden.EN_PREPARACION],
            EstadoOrden.EN_PREPARACION: [EstadoOrden.ENVIADA],
            EstadoOrden.ENVIADA: [EstadoOrden.ENTREGADA]
        }
        
        estado_nuevo = EstadoOrden[nuevo_estado]

        if estado_nuevo not in transiciones_validas.get(self.status, []):
            raise InvalidStateTransitionException("Está prohibido saltar estados.")

        self.status = estado_nuevo

        # Generar factura solo en estado PAGADA
        if self.status == EstadoOrden.PAGADA:
            self.factura = Factura("UUID-12345", "XAXX010101000", "BLOB_XML")

# --- Pruebas Unitarias de Finanzas (TDD) ---

def test_calcular_total_orden_con_iva_y_descuento():
    orden = Orden()
    # Agregamos una línea con subtotal de 100
    orden.agregarLinea(LineaPedido(producto_id=1, cantidad=1, precio_unitario=100))
    
    # Aplicamos descuento de 20 (para simular el 20% de 100)
    orden.aplicarCupon(20)
    
    # Asserts that 100 - 20% discount + 16% IVA strictly equals 92.80
    assert round(orden.total, 2) == 92.80

def test_transicion_estado_invalida_lanza_excepcion():
    orden = Orden()
    
    # Asserts trying to change CREADA directly to ENTREGADA throws error
    with pytest.raises(InvalidStateTransitionException):
        orden.avanzarEstado("ENTREGADA")
