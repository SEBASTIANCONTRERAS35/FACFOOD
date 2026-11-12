"""Rebanada Checkout (Sebastián): crear orden, cupón, entrega y pago. Vista 04.

Lleva la orden de CREADA a PAGADA. De PAGADA en adelante es de Arturo.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Header, Request, status
from fastapi.concurrency import run_in_threadpool

from app.checkout import servicio
from app.checkout.esquemas import (
    EJEMPLO_ORDEN,
    CrearOrdenEntrada,
    CuponEntrada,
    CuponesSalida,
    EntregaEntrada,
    OrdenResumen,
    OrdenSalida,
    PagoEntrada,
    Ref,
    SesionPagoSalida,
)
from app.shared.auth import UsuarioActual, get_usuario_actual
from app.ports.pagos import FirmaInvalida, PasarelaDePago
from app.shared.config import obtener_config
from app.shared.errores import ErrorDeAplicacion, respuesta_error
from app.shared.pasarela import obtener_pasarela
from app.shared.uow import FabricaUoW, obtener_fabrica_uow

router = APIRouter(tags=["Checkout"])
log = logging.getLogger(__name__)


@router.get(
    "/usuarios/me/ordenes", response_model=list[OrdenResumen], tags=["Mis pedidos"],
    summary="Mis pedidos, del más reciente al más antiguo",
    responses={401: respuesta_error(401, "NO_AUTENTICADO", "Inicia sesión para continuar", "/usuarios/me/ordenes")},
)
def mis_ordenes(actual: UsuarioActual = Depends(get_usuario_actual), fabrica: FabricaUoW = Depends(obtener_fabrica_uow)):
    """Solo los pedidos del usuario de la sesión, desde que se pagan. No incluye los carritos que no se
    pagaron (CREADA) ni datos de otros usuarios. Para el detalle y la línea de tiempo: `GET /ordenes/{id}`."""
    return servicio.mis_ordenes(fabrica, actual)


@router.get(
    "/cupones", response_model=CuponesSalida, tags=["Cupones"],
    summary="Mi nivel de lealtad y los cupones que puedo usar",
    responses={401: respuesta_error(401, "NO_AUTENTICADO", "Inicia sesión para continuar", "/cupones")},
)
def cupones(actual: UsuarioActual = Depends(get_usuario_actual), fabrica: FabricaUoW = Depends(obtener_fabrica_uow)):
    """Filtrado para el usuario de la sesión: oculta los vencidos y agotados, el de bienvenida solo aparece
    a quien no ha completado pedidos, y los de un uso por persona que ya usó salen como `usado`.
    El DTO no expone los contadores internos de uso del cupón."""
    return servicio.cupones_del_usuario(fabrica, actual)


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
          fabrica: FabricaUoW = Depends(obtener_fabrica_uow), pasarela: PasarelaDePago = Depends(obtener_pasarela)):
    """En una sola transacción: bloquea la orden y el cupón (`SELECT … FOR UPDATE`), consume el cupón
    solo si fue el descuento aplicado, pasa a **PAGADA**, genera la factura y, si es entrega estudiante,
    el código de 4 dígitos. Si algo falla, la orden sigue CREADA.

    Solo existe con la pasarela `simulado`: con `stripe` responde **409 PAGO_EN_LINEA_REQUERIDO**
    y la orden se paga con `POST /ordenes/{id}/checkout`."""
    return servicio.pagar(fabrica, actual, orden_id, datos.rfc if datos else None, pasarela)


@router.post(
    "/ordenes/{orden_id}/checkout", response_model=SesionPagoSalida, tags=["Pagos"],
    summary="Iniciar el pago: abre el cobro en la pasarela con el monto del servidor",
    responses={
        404: respuesta_error(404, "NO_ENCONTRADO", "Esa orden no existe", "/ordenes/5/checkout"),
        409: respuesta_error(409, "ORDEN_YA_PAGADA", "Esta orden ya fue pagada", "/ordenes/5/checkout"),
        422: respuesta_error(422, "CUPON_INVALIDO", "El cupón ya alcanzó su límite de usos", "/ordenes/5/checkout"),
        502: respuesta_error(502, "PASARELA_NO_DISPONIBLE", "No se pudo iniciar el pago con tarjeta",
                             "/ordenes/5/checkout"),
    },
)
def iniciar_pago(orden_id: int, datos: PagoEntrada | None = None, actual: UsuarioActual = Depends(get_usuario_actual),
                 fabrica: FabricaUoW = Depends(obtener_fabrica_uow),
                 pasarela: PasarelaDePago = Depends(obtener_pasarela)):
    """Revalida todo (puesto abierto, lealtad, cupón) y fija el monto. Con **stripe** crea una sesión de
    Stripe Checkout (MXN, expira en 30 min) y devuelve su `url`; mientras esté abierta, la orden no se
    puede editar (409 PAGO_EN_CURSO) y repetir la llamada devuelve la misma sesión. Con **simulado**
    devuelve `url: null` y el pago se confirma con `POST /ordenes/{id}/pagar`.

    La orden pasa a PAGADA cuando Stripe avisa al webhook, no cuando el navegador regresa."""
    return servicio.iniciar_pago(fabrica, pasarela, actual, orden_id, obtener_config().url_frontend,
                                 datos.rfc if datos else None)


@router.delete(
    "/ordenes/{orden_id}/checkout", response_model=OrdenSalida, tags=["Pagos"],
    summary="Cancelar el pago en curso para volver a editar el pedido",
    responses={409: respuesta_error(409, "PAGO_YA_REALIZADO",
                                    "Tu pago ya se realizó; en un momento verás tu pedido confirmado",
                                    "/ordenes/5/checkout")},
)
def cancelar_pago(orden_id: int, actual: UsuarioActual = Depends(get_usuario_actual),
                  fabrica: FabricaUoW = Depends(obtener_fabrica_uow),
                  pasarela: PasarelaDePago = Depends(obtener_pasarela)):
    """Expira la sesión en Stripe. Si el comprador ya pagó, responde 409 y la orden se confirma con el aviso."""
    return servicio.cancelar_pago(fabrica, pasarela, actual, orden_id)


TAMANO_MAXIMO_AVISO = 256 * 1024


@router.post(
    "/pagos/webhook", tags=["Pagos"], status_code=status.HTTP_200_OK,
    summary="Avisos de Stripe (firmados). No lo llama el frontend",
    responses={400: respuesta_error(400, "FIRMA_INVALIDA", "Firma inválida", "/pagos/webhook")},
)
async def webhook(request: Request, stripe_signature: Annotated[str | None, Header()] = None,
                  fabrica: FabricaUoW = Depends(obtener_fabrica_uow),
                  pasarela: PasarelaDePago = Depends(obtener_pasarela)):
    """Público a propósito (Stripe no inicia sesión), pero **autenticado por la firma**: se verifica el
    encabezado `Stripe-Signature` (HMAC-SHA256 con `STRIPE_WEBHOOK_SECRET`, máximo 5 min de antigüedad)
    sobre el cuerpo crudo antes de leerlo. Sin firma válida: 400 y no se toca nada.

    Idempotente: el mismo aviso puede llegar varias veces. Además se comprueba que la orden, la moneda
    y el monto del aviso coincidan con el pago guardado."""
    cuerpo = await request.body()
    if len(cuerpo) > TAMANO_MAXIMO_AVISO:
        raise _FirmaRechazada("Aviso demasiado grande")
    try:
        evento = pasarela.leer_evento(cuerpo, stripe_signature)
    except FirmaInvalida:
        raise _FirmaRechazada("Firma inválida")
    resultado = await run_in_threadpool(servicio.procesar_evento, fabrica, pasarela, evento)
    log.info("Aviso de pago %s: %s", evento.id, resultado)
    return {"recibido": True}


class _FirmaRechazada(ErrorDeAplicacion):
    status = 400
    codigo = "FIRMA_INVALIDA"
