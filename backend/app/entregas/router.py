"""Endpoints de reparto para las vistas 07 y 08."""
from fastapi import APIRouter, Depends, status

from app.shared.auth import UsuarioActual, exigir_rol
from app.shared.uow import FabricaUoW, obtener_fabrica_uow
from app.entregas.esquemas import EntregaAceptadaSalida, ListaEntregasDisponibles
from app.entregas.servicio import aceptar, disponibles

router = APIRouter(tags=["Entregas"])

@router.get("/entregas/disponibles", response_model=ListaEntregasDisponibles)
def get_disponibles(
    fabrica: FabricaUoW = Depends(obtener_fabrica_uow),
    actual: UsuarioActual = Depends(exigir_rol("repartidor")),
):
    return disponibles(fabrica, actual)

@router.post(
    "/entregas/{orden_id}/aceptar",
    response_model=EntregaAceptadaSalida,
    status_code=status.HTTP_201_CREATED,
)
def post_aceptar(
    orden_id: int,
    fabrica: FabricaUoW = Depends(obtener_fabrica_uow),
    actual: UsuarioActual = Depends(exigir_rol("repartidor")),
):
    return aceptar(fabrica, actual, orden_id)
