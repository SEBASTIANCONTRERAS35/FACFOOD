"""Esquemas de respuesta de la vista 05."""
from datetime import datetime
from pydantic import BaseModel
from app.checkout.esquemas import OrdenSalida
class EventoSalida(BaseModel):
    estado: str
    actor_id: int | None
    creado_en: datetime
class SeguimientoSalida(OrdenSalida):
    eventos: list[EventoSalida]
