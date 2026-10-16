"""Rebanada Checkout (Sebastián): crear orden, cupón, entrega y pago. Vista 04.

Lleva la orden de CREADA a PAGADA. De PAGADA en adelante es de Arturo.
"""

from fastapi import APIRouter, Depends, status

from app.checkout import servicio
from app.checkout.esquemas import CrearOrdenEntrada, CuponEntrada, EntregaEntrada, OrdenSalida, PagoEntrada, Ref
from app.shared.auth import UsuarioActual, get_usuario_actual
from app.shared.uow import FabricaUoW, obtener_fabrica_uow

router = APIRouter(tags=["Checkout"])


@router.get("/destinos", response_model=list[Ref], summary="Facultades y edificios para la entrega")
def destinos(fabrica: FabricaUoW = Depends(obtener_fabrica_uow)):
    return servicio.destinos(fabrica)


@router.post("/ordenes", response_model=OrdenSalida, status_code=status.HTTP_201_CREATED,
             summary="Crear la orden (estado CREADA) con precios del servidor")
def crear(datos: CrearOrdenEntrada, actual: UsuarioActual = Depends(get_usuario_actual),
          fabrica: FabricaUoW = Depends(obtener_fabrica_uow)):
    return servicio.crear_orden(
        fabrica, actual, datos.punto_venta_id,
        [(l.producto_id, l.cantidad) for l in datos.lineas], datos.metodo_entrega, datos.destino_id,
    )


@router.patch("/ordenes/{orden_id}/entrega", response_model=OrdenSalida,
              summary="Cambiar entre Pickup y Entrega estudiante")
def cambiar_entrega(orden_id: int, datos: EntregaEntrada, actual: UsuarioActual = Depends(get_usuario_actual),
                    fabrica: FabricaUoW = Depends(obtener_fabrica_uow)):
    return servicio.cambiar_entrega(fabrica, actual, orden_id, datos.metodo_entrega, datos.destino_id)


@router.post("/ordenes/{orden_id}/cupon", response_model=OrdenSalida,
             summary="Aplicar cupón (se usa el mayor entre cupón y lealtad)")
def aplicar_cupon(orden_id: int, datos: CuponEntrada, actual: UsuarioActual = Depends(get_usuario_actual),
                  fabrica: FabricaUoW = Depends(obtener_fabrica_uow)):
    return servicio.aplicar_cupon(fabrica, actual, orden_id, datos.codigo)


@router.delete("/ordenes/{orden_id}/cupon", response_model=OrdenSalida, summary="Quitar el cupón")
def quitar_cupon(orden_id: int, actual: UsuarioActual = Depends(get_usuario_actual),
                 fabrica: FabricaUoW = Depends(obtener_fabrica_uow)):
    return servicio.quitar_cupon(fabrica, actual, orden_id)


@router.post("/ordenes/{orden_id}/pagar", response_model=OrdenSalida,
             summary="Pago simulado: CREADA -> PAGADA y genera la factura")
def pagar(orden_id: int, datos: PagoEntrada | None = None, actual: UsuarioActual = Depends(get_usuario_actual),
          fabrica: FabricaUoW = Depends(obtener_fabrica_uow)):
    return servicio.pagar(fabrica, actual, orden_id, datos.rfc if datos else None)
