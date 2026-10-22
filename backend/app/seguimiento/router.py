"""Rebanada Seguimiento (Arturo): estado de la orden y factura. Vista 05."""
from fastapi import APIRouter, Depends, Response
from app.seguimiento import servicio
from app.seguimiento.esquemas import SeguimientoSalida
from app.shared.auth import UsuarioActual, get_usuario_actual
from app.shared.uow import FabricaUoW, obtener_fabrica_uow
router = APIRouter(tags=["Seguimiento"])
@router.get("/ordenes/{orden_id}", response_model=SeguimientoSalida)
def consultar_orden(orden_id: int, actual: UsuarioActual = Depends(get_usuario_actual), fabrica: FabricaUoW = Depends(obtener_fabrica_uow)):
    return servicio.seguimiento(fabrica, actual, orden_id)
@router.get("/ordenes/{orden_id}/factura")
def descargar_factura(orden_id: int, actual: UsuarioActual = Depends(get_usuario_actual), fabrica: FabricaUoW = Depends(obtener_fabrica_uow)):
    return Response(content=servicio.factura_xml(fabrica, actual, orden_id), media_type="application/xml", headers={"Content-Disposition": f'attachment; filename="factura-facfood-{orden_id}.xml"'})
