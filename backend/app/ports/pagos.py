"""Puerto de la pasarela de pago — arquitectura hexagonal.

El checkout solo conoce esta interfaz. Hay dos adaptadores (app/adapters/pagos):
  - PagoSimulado: no cobra; el pago se confirma con POST /ordenes/{id}/pagar (desarrollo y demo)
  - PagoStripe:   Stripe Checkout en modo de prueba; el pago se confirma con el webhook firmado

Se elige con FACFOOD_PASARELA=simulado|stripe. Ver ADR_004.md.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol

ESTADOS_PAGO = ("PENDIENTE", "PAGADO", "FALLIDO", "EXPIRADO")


@dataclass
class PagoRegistro:
    id: int | None
    orden_id: int
    proveedor: str  # "simulado" | "stripe"
    referencia: str | None  # id de la sesión en la pasarela
    monto: Decimal  # lo que se le pidió cobrar a la pasarela (MXN)
    estado: str = "PENDIENTE"
    url: str | None = None
    expira_en: datetime | None = None
    rfc: str | None = None  # para la factura; None = público en general
    evento_id: str | None = None  # último evento de la pasarela que cambió el estado
    creado_en: datetime | None = None
    actualizado_en: datetime | None = None


@dataclass(frozen=True)
class SesionDePago:
    referencia: str
    url: str | None  # a dónde se redirige al comprador; None en el simulado


@dataclass(frozen=True)
class EventoDePago:
    """Un aviso de la pasarela, ya con la firma verificada."""

    id: str
    tipo: str  # "pagado" | "expirado" | "fallido" | "ignorado"
    referencia: str | None = None
    orden_id: int | None = None
    monto: Decimal | None = None
    moneda: str | None = None


class FirmaInvalida(Exception):
    """El aviso no viene de la pasarela (firma ausente, alterada o vencida)."""


class PasarelaNoDisponible(Exception):
    """La pasarela no respondió o rechazó la operación."""


class PasarelaDePago(Protocol):
    nombre: str
    redirige: bool  # True: el comprador paga en la página de la pasarela

    def crear_sesion(
        self, *, pago_id: int, orden_id: int, monto: Decimal, descripcion: str, correo: str | None,
        url_exito: str, url_cancelar: str, expira_en: datetime,
    ) -> SesionDePago: ...

    def cancelar_sesion(self, referencia: str) -> bool:
        """Cierra la sesión para que ya no se pueda pagar. False si ya se había pagado."""
        ...

    def leer_evento(self, cuerpo: bytes, firma: str | None) -> EventoDePago:
        """Verifica la firma y traduce el aviso. Lanza FirmaInvalida si no es auténtico."""
        ...


class PagoRepo(Protocol):
    def agregar(self, registro: PagoRegistro) -> PagoRegistro: ...
    def guardar(self, registro: PagoRegistro) -> None: ...
    def por_referencia(self, proveedor: str, referencia: str, bloquear: bool = False) -> PagoRegistro | None: ...
    def pendiente_de_orden(self, orden_id: int, bloquear: bool = False) -> PagoRegistro | None: ...
    def de_orden(self, orden_id: int) -> list[PagoRegistro]: ...
