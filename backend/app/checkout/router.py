"""Rebanada Checkout (Sebastián): crear orden, cupón, entrega y pago. Vista 04.

Lleva la orden de CREADA a PAGADA. De PAGADA en adelante es de Arturo.
"""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, status

from app.checkout import servicio
from app.checkout.esquemas import (
    EJEMPLO_ORDEN,
    CrearOrdenEntrada,
    CuponEntrada,
    EntregaEntrada,
    OrdenSalida,
    PagoEntrada,
    Ref,
)
from app.shared.auth import UsuarioActual, get_usuario_actual
from app.shared.errores import respuesta_error
from app.shared.uow import FabricaUoW, obtener_fabrica_uow

router = APIRouter(tags=["Checkout"])


@router.get("/destinos", response_model=list[Ref], summary="Facultades y edificios para la entrega")
def destinos(fabrica: FabricaUoW = Depends(obtener_fabrica_uow)):
    return servicio.destinos(fabrica)


EJEMPLOS_CREAR = {
    "pickup": {
        "summary": "Pickup: 2 tacos de pastor y 1 quesadilla",
        "value": {"punto_venta_id": 1, "lineas": [{"producto_id": 1, "cantidad": 2}, {"producto_id": 3, "cantidad": 1}],
                  "metodo_entrega": "pickup"},
    },
    "estudiante": {
        "summary": "Entrega estudiante a la Facultad de Arquitectura",
        "value": {"punto_venta_id": 1, "lineas": [{"producto_id": 2, "cantidad": 3}], "metodo_entrega": "estudiante",
                  "destino_id": 2},
    },
    "invalido": {
        "summary": "Inválido: cantidad 0 y sin puesto (para ver el 400)",
        "value": {"lineas": [{"producto_id": 1, "cantidad": 0}]},
    },
}


@router.post(
    "/ordenes", response_model=OrdenSalida, status_code=status.HTTP_201_CREATED,
    summary="Crear la orden (estado CREADA) con precios del servidor",
    responses={
        201: {"description": "Orden creada", "content": {"application/json": {"example": EJEMPLO_ORDEN}}},
        400: respuesta_error(400, "VALIDACION", "Uno o más campos del payload no cumplen con las reglas establecidas.",
                             "/ordenes", invalid_params=[
                                 {"name": "punto_venta_id", "reason": "Field required"},
                                 {"name": "lineas.0.cantidad", "reason": "Input should be greater than 0"}]),
        401: respuesta_error(401, "NO_AUTENTICADO", "Inicia sesión para continuar", "/ordenes"),
        404: respuesta_error(404, "NO_ENCONTRADO", "Ese puesto no existe", "/ordenes"),
        409: respuesta_error(409, "PUESTO_CERRADO", "Quesadillas Las Islas está cerrado en este momento", "/ordenes"),
        422: respuesta_error(422, "PRODUCTO_NO_ENCONTRADO", "Producto inexistente: 6", "/ordenes"),
    },
)
def crear(
    datos: Annotated[CrearOrdenEntrada, Body(openapi_examples=EJEMPLOS_CREAR)],
    actual: UsuarioActual = Depends(get_usuario_actual),
    fabrica: FabricaUoW = Depends(obtener_fabrica_uow),
):
    """**Endpoint crítico (dinero).** El cliente manda solo IDs y cantidades; el servidor toma el precio
    del catálogo del puesto, aplica la lealtad del comprador y calcula el envío con la estrategia de
    entrega (Pickup $0 · Entrega estudiante $5/km, distancia con PostGIS). La orden queda **CREADA**.

    - **400** el JSON no cumple el DTO (cantidad fuera de 1–50, faltan campos…), con `invalid_params`.
    - **409** el puesto está cerrado · **422** producto de otro puesto, sin entrega o sin destino.
    """
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


@router.post(
    "/ordenes/{orden_id}/pagar", response_model=OrdenSalida,
    summary="Pago simulado: CREADA -> PAGADA y genera la factura",
    responses={
        404: respuesta_error(404, "NO_ENCONTRADO", "Esa orden no existe", "/ordenes/5/pagar"),
        409: respuesta_error(409, "ORDEN_YA_PAGADA", "Esta orden ya fue pagada", "/ordenes/5/pagar"),
        422: respuesta_error(422, "CUPON_INVALIDO", "El cupón ya alcanzó su límite de usos", "/ordenes/5/pagar"),
    },
)
def pagar(orden_id: int, datos: PagoEntrada | None = None, actual: UsuarioActual = Depends(get_usuario_actual),
          fabrica: FabricaUoW = Depends(obtener_fabrica_uow)):
    """En una sola transacción: bloquea la orden y el cupón (`SELECT … FOR UPDATE`), consume el cupón
    solo si fue el descuento aplicado, pasa a **PAGADA**, genera la factura y, si es entrega estudiante,
    el código de 4 dígitos. Si algo falla, la orden sigue CREADA."""
    return servicio.pagar(fabrica, actual, orden_id, datos.rfc if datos else None)
