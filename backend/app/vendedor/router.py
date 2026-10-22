from fastapi import APIRouter,Depends
from app.shared.auth import UsuarioActual,exigir_rol
from app.shared.uow import FabricaUoW,obtener_fabrica_uow
from app.vendedor.esquemas import *
from app.vendedor.servicio import *
router=APIRouter(tags=["Vendedor"])
@router.get("/vendedor/ordenes",response_model=PanelVendedor)
def ordenes(f:FabricaUoW=Depends(obtener_fabrica_uow),u:UsuarioActual=Depends(exigir_rol("vendedor"))): return listar_ordenes(f,u)
@router.post("/ordenes/{i}/estado")
def estado(i:int,e:CambioEstadoEntrada,f:FabricaUoW=Depends(obtener_fabrica_uow),u:UsuarioActual=Depends(exigir_rol("vendedor"))): return cambiar_estado(f,u,i,e.estado)
@router.patch("/puntos-venta/{i}",response_model=PuntoVentaSalida)
def punto(i:int,e:PuntoVentaEntrada,f:FabricaUoW=Depends(obtener_fabrica_uow),u:UsuarioActual=Depends(exigir_rol("vendedor"))): return cambiar_punto(f,u,i,e.abierto)
