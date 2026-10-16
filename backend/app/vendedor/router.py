"""Rebanada Vendedor (Arturo): panel del puesto. Vista 06.

Pendiente — ver docs/CONTRATO.md:
  GET   /vendedor/ordenes
  POST  /ordenes/{id}/estado        PAGADA -> EN_PREPARACION -> ENVIADA
  PATCH /puntos-venta/{id}          abierto / cerrado
"""

from fastapi import APIRouter

router = APIRouter(tags=["Vendedor"])
