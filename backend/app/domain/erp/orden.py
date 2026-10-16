"""
Capa de Dominio - FACFOOD
Módulo ERP: Orden, líneas de pedido y reglas financieras

Reglas (lección 2.3 del curso):
- Total = (Subtotal - Descuentos) + IVA(16%) + Envío. El IVA se calcula sobre
  el monto ya con descuento; el envío no causa IVA aquí.
- Máquina de estados estricta e irreversible:
  CREADA -> PAGADA -> EN_PREPARACION -> ENVIADA -> ENTREGADA
  CREADA -> CANCELADA. Está prohibido saltar estados.
- Nunca se confía en el frontend: el cliente envía IDs de producto y el
  servidor dicta el precio desde el catálogo. agregar_linea() no recibe precio.
- La factura solo se genera en estado PAGADA.
- Marketplace: el pago se divide entre plataforma y vendedor.
- Dinero con Decimal (nunca float) y redondeo a centavos.
"""

import enum
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Mapping

from app.domain.crm.retencion import Cupon

from .factura import Factura, emitir_factura

CENTAVO = Decimal("0.01")
TASA_IVA = Decimal("0.16")
CERO = Decimal("0.00")


def _redondear(monto: Decimal) -> Decimal:
    return monto.quantize(CENTAVO, rounding=ROUND_HALF_UP)


class EstadoOrden(str, enum.Enum):
    CREADA = "CREADA"
    PAGADA = "PAGADA"
    EN_PREPARACION = "EN_PREPARACION"
    ENVIADA = "ENVIADA"
    ENTREGADA = "ENTREGADA"
    CANCELADA = "CANCELADA"


TRANSICIONES = {
    EstadoOrden.CREADA: {EstadoOrden.PAGADA, EstadoOrden.CANCELADA},
    EstadoOrden.PAGADA: {EstadoOrden.EN_PREPARACION},
    EstadoOrden.EN_PREPARACION: {EstadoOrden.ENVIADA},
    EstadoOrden.ENVIADA: {EstadoOrden.ENTREGADA},
    EstadoOrden.ENTREGADA: set(),
    EstadoOrden.CANCELADA: set(),
}

ESTADOS_PAGADOS = {
    EstadoOrden.PAGADA,
    EstadoOrden.EN_PREPARACION,
    EstadoOrden.ENVIADA,
    EstadoOrden.ENTREGADA,
}


class InvalidStateTransitionException(Exception):
    """Transición de estado no permitida (por ejemplo, saltar de CREADA a ENTREGADA)."""


class OrdenInmutableError(Exception):
    """La orden ya no se puede modificar porque salió del estado CREADA."""


class OrdenVaciaError(Exception):
    """No se puede pagar una orden sin líneas."""


class ProductoNoEncontradoError(Exception):
    """El ID de producto no existe en el catálogo del servidor."""


class FacturaNoPermitidaError(Exception):
    """La factura solo se genera una vez y únicamente en estado PAGADA."""


class OrdenNoPagadaError(Exception):
    """La operación requiere una orden que ya fue pagada."""


@dataclass(frozen=True)
class LineaPedido:
    producto_id: str
    cantidad: int
    precio_unitario: Decimal

    @property
    def subtotal(self) -> Decimal:
        return _redondear(self.precio_unitario * self.cantidad)


@dataclass(frozen=True)
class DivisionPago:
    base: Decimal
    comision_plataforma: Decimal
    retencion: Decimal
    neto_vendedor: Decimal


class Orden:
    def __init__(self, catalogo: Mapping[str, Decimal], fecha: date | None = None):
        self._catalogo = catalogo
        self.fecha = fecha or date.today()
        self.estado = EstadoOrden.CREADA
        self._lineas: list[LineaPedido] = []
        self._cupon: Cupon | None = None
        self._descuento = CERO
        self._envio = CERO
        self._factura: Factura | None = None
        self._pedidos_completados = 0

    @classmethod
    def restaurar(
        cls,
        catalogo: Mapping[str, Decimal],
        fecha: date,
        estado,
        lineas: list[LineaPedido],
        descuento: Decimal,
        envio: Decimal,
        cupon: Cupon | None = None,
        pedidos_completados: int = 0,
    ) -> "Orden":
        """Reconstruye una orden guardada (adaptador de persistencia).

        El descuento se restaura tal cual se guardó: en una orden ya pagada el
        cupón pudo agotarse después, y recalcularlo cambiaría el cobro histórico.
        """
        orden = cls(catalogo, fecha)
        orden.estado = cls._a_estado(estado)
        orden._lineas = list(lineas)
        orden._cupon = cupon
        orden._descuento = _redondear(Decimal(str(descuento)))
        orden._envio = _redondear(Decimal(str(envio)))
        orden._pedidos_completados = pedidos_completados
        return orden

    @property
    def cupon(self) -> Cupon | None:
        return self._cupon

    # ---- Edición (solo mientras la orden está CREADA) ----
    def _exigir_creada(self) -> None:
        if self.estado is not EstadoOrden.CREADA:
            raise OrdenInmutableError(
                f"La orden está {self.estado.value} y ya no se puede modificar"
            )

    def agregar_linea(self, producto_id: str, cantidad: int) -> None:
        """El precio lo dicta el catálogo del servidor, nunca el cliente."""
        self._exigir_creada()
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor a cero")
        if producto_id not in self._catalogo:
            raise ProductoNoEncontradoError(f"Producto inexistente: {producto_id}")
        precio = Decimal(str(self._catalogo[producto_id]))
        self._lineas.append(LineaPedido(producto_id, cantidad, precio))
        self._recalcular_descuento()

    def aplicar_cupon(self, cupon: Cupon) -> None:
        self._exigir_creada()
        self._cupon = cupon
        self._recalcular_descuento()

    def definir_envio(self, monto: Decimal) -> None:
        self._exigir_creada()
        if monto < 0:
            raise ValueError("El envío no puede ser negativo")
        self._envio = _redondear(Decimal(str(monto)))

    def _recalcular_descuento(self) -> None:
        if self._cupon is None:
            self._descuento = CERO
            return
        descuento = self._cupon.calcular_descuento(float(self.subtotal), self.fecha)
        self._descuento = _redondear(Decimal(str(descuento)))

    # ---- Cálculo financiero ----
    @property
    def lineas(self) -> tuple[LineaPedido, ...]:
        return tuple(self._lineas)

    @property
    def subtotal(self) -> Decimal:
        return sum((l.subtotal for l in self._lineas), CERO)

    @property
    def descuentos(self) -> Decimal:
        return self._descuento

    @property
    def iva(self) -> Decimal:
        return _redondear((self.subtotal - self._descuento) * TASA_IVA)

    @property
    def envio(self) -> Decimal:
        return self._envio

    @property
    def total(self) -> Decimal:
        return _redondear((self.subtotal - self._descuento) + self.iva + self._envio)

    # ---- Máquina de estados ----
    def avanzar_estado(self, nuevo) -> None:
        destino = self._a_estado(nuevo)
        if destino not in TRANSICIONES[self.estado]:
            raise InvalidStateTransitionException(
                f"No se puede pasar de {self.estado.value} a {destino.value}"
            )
        if destino is EstadoOrden.PAGADA:
            if not self._lineas:
                raise OrdenVaciaError("No se puede pagar una orden sin líneas")
            # Se revalida el cupón al pagar y solo entonces se consume
            self._recalcular_descuento()
            if self._cupon is not None:
                self._cupon.registrar_uso()
        self.estado = destino

    @staticmethod
    def _a_estado(valor) -> EstadoOrden:
        try:
            return EstadoOrden(valor)
        except ValueError:
            raise InvalidStateTransitionException(f"Estado desconocido: {valor!r}")

    # ---- Factura ----
    @property
    def factura(self) -> Factura | None:
        return self._factura

    def generar_factura(self, rfc_receptor: str) -> Factura:
        if self.estado is not EstadoOrden.PAGADA:
            raise FacturaNoPermitidaError("La factura solo se genera en estado PAGADA")
        if self._factura is not None:
            raise FacturaNoPermitidaError("La orden ya tiene factura")
        self._factura = emitir_factura(
            rfc_receptor, self.fecha, self._lineas, self.subtotal,
            self._descuento, self.iva, self._envio, self.total,
        )
        return self._factura

    # ---- Marketplace: pago dividido ----
    def dividir_pago(self, comision_pct: Decimal, retencion_pct: Decimal = Decimal("0")) -> DivisionPago:
        """Divide la base (subtotal - descuentos) entre plataforma y vendedor.

        IVA y envío se llevan aparte. Los porcentajes son parámetros: la
        comisión y la retención fiscal deben definirse con el equipo/profe.
        """
        if self.estado not in ESTADOS_PAGADOS:
            raise OrdenNoPagadaError("Solo se divide el pago de órdenes ya pagadas")
        if comision_pct < 0 or retencion_pct < 0 or comision_pct + retencion_pct > 100:
            raise ValueError("Porcentajes inválidos")
        base = self.subtotal - self._descuento
        comision = _redondear(base * Decimal(str(comision_pct)) / 100)
        retencion = _redondear(base * Decimal(str(retencion_pct)) / 100)
        return DivisionPago(base, comision, retencion, base - comision - retencion)
