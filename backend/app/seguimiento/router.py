"""Rebanada Seguimiento (Arturo): estado de la orden y factura. Vista 05.

Pendiente — ver docs/CONTRATO.md:
  GET /ordenes/{id}           orden + historial de orden_eventos
  GET /ordenes/{id}/factura   XML de la factura (se genera al pagar)
"""

from fastapi import APIRouter

router = APIRouter(tags=["Seguimiento"])
