"""Endpoints de reparto para las vistas 07 y 08."""
from fastapi import APIRouter, Depends, status

from app.entregas.esquemas import (
    CodigoEntregaEntrada,
    EntregaAceptadaSalida,
    EntregaDetalleSalida,
    ListaEntregasDisponibles,
)
from app.entregas.servicio import aceptar, disponibles, detalle, entregar, recoger
from app.shared.auth import UsuarioActual, exigir_rol
from app.shared.uow import FabricaUoW, obtener_fabrica_uow

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

@router.get("/entregas/{orden_id}", response_model=EntregaDetalleSalida)
def get_detalle(
    orden_id: int,
    fabrica: FabricaUoW = Depends(obtener_fabrica_uow),
    actual: UsuarioActual = Depends(exigir_rol("repartidor")),
):
    return detalle(fabrica, actual, orden_id)

@router.post("/entregas/{orden_id}/recoger", response_model=EntregaDetalleSalida)
def post_recoger(
    orden_id: int,
    fabrica: FabricaUoW = Depends(obtener_fabrica_uow),
    actual: UsuarioActual = Depends(exigir_rol("repartidor")),
):
    return recoger(fabrica, actual, orden_id)

@router.post("/entregas/{orden_id}/entregar", response_model=EntregaDetalleSalida)
def post_entregar(
    orden_id: int,
    entrada: CodigoEntregaEntrada,
    fabrica: FabricaUoW = Depends(obtener_fabrica_uow),
    actual: UsuarioActual = Depends(exigir_rol("repartidor")),
):
    return entregar(fabrica, actual, orden_id, entrada.codigo_entrega)
