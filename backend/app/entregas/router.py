"""Rebanada Entregas (Arturo): modo repartidor. Vistas 07 y 08.

Pendiente — ver docs/CONTRATO.md:
  GET  /entregas/disponibles
  POST /entregas/{orden_id}/aceptar | /recoger | /entregar (con codigo_entrega)
"""

from fastapi import APIRouter

router = APIRouter(tags=["Entregas"])
