"""Rebanada Checkout (Sebastián): crear orden, cupón, entrega y pago. Vista 04.

Lleva la orden de CREADA a PAGADA. De PAGADA en adelante es de Arturo.
"""

from fastapi import APIRouter

router = APIRouter(tags=["Checkout"])
