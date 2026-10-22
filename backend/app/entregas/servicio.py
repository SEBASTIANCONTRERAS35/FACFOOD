from dataclasses import replace
from datetime import datetime, timezone

from app.domain.erp.orden import EstadoOrden
from app.ports.repositorios import EntregaRegistro, EventoOrden
from app.shared.auth import UsuarioActual
from app.shared.dinero import a_texto
from app.shared.errores import Conflicto, DatosInvalidos, NoEncontrado
from app.shared.uow import FabricaUoW

ESTADOS_ELEGIBLES = {EstadoOrden.PAGADA, EstadoOrden.EN_PREPARACION}

def disponibles(fabrica: FabricaUoW, repartidor: UsuarioActual) -> dict:
    with fabrica() as uow:
        salida = []
        for registro in uow.entregas.ordenes_disponibles():
            punto = uow.puntos_venta.por_id(registro.punto_venta_id)
            destino = uow.destinos.por_id(registro.destino_id) if registro.destino_id else None
            productos = {p.id: p for p in uow.productos.de_punto(registro.punto_venta_id)}
            salida.append({
                "orden_id": registro.id,
                "estado": registro.orden.estado.value,
                "puesto": punto.nombre,
                "lugar_recogida": punto.ubicacion_texto,
                "destino": destino.nombre if destino else None,
                "lineas": [
                    {"nombre": productos[int(linea.producto_id)].nombre if int(linea.producto_id) in productos else "",
                     "cantidad": linea.cantidad}
                    for linea in registro.orden.lineas
                ],
                "distancia_km": a_texto(registro.distancia_km),
                "ganancia": a_texto(registro.orden.envio),
            })
        return {"entregas": salida}

def aceptar(fabrica: FabricaUoW, repartidor: UsuarioActual, orden_id: int) -> dict:
    with fabrica() as uow:
        orden = uow.ordenes.por_id(orden_id, bloquear=True)
        if orden is None:
            raise NoEncontrado("La orden no existe")
        if orden.metodo_entrega != "estudiante" or orden.orden.estado not in ESTADOS_ELEGIBLES:
            raise Conflicto("La orden ya no está disponible para reparto", "ENTREGA_NO_DISPONIBLE")
        if uow.entregas.por_orden(orden_id) is not None:
            raise Conflicto("La orden ya fue aceptada por otro repartidor", "ENTREGA_YA_ACEPTADA")
        ahora = datetime.now(timezone.utc)
        uow.entregas.agregar(EntregaRegistro(
            id=None, orden_id=orden_id, repartidor_id=repartidor.id,
            estado="ACEPTADA", aceptada_en=ahora,
        ))
        uow.commit()
        return {"orden_id": orden_id, "estado": "ACEPTADA"}

def _entrega_asignada(uow, repartidor: UsuarioActual, orden_id: int, bloquear: bool):
    orden = uow.ordenes.por_id(orden_id, bloquear=bloquear)
    if orden is None or orden.metodo_entrega != "estudiante":
        raise NoEncontrado("La entrega no existe")
    entrega = uow.entregas.por_orden(orden_id)
    if entrega is None or entrega.repartidor_id != repartidor.id:
        raise NoEncontrado("La entrega no existe")
    return orden, entrega

def _detalle(uow, orden, entrega) -> dict:
    punto = uow.puntos_venta.por_id(orden.punto_venta_id)
    destino = uow.destinos.por_id(orden.destino_id) if orden.destino_id else None
    productos = {p.id: p for p in uow.productos.de_punto(orden.punto_venta_id)}
    return {
        "orden_id": orden.id,
        "estado_orden": orden.orden.estado.value,
        "estado_entrega": entrega.estado,
        "puesto": {
            "nombre": punto.nombre, "ubicacion": punto.ubicacion_texto,
            "lat": punto.lat, "lon": punto.lon,
        },
        "destino": ({
            "nombre": destino.nombre, "lat": destino.lat, "lon": destino.lon,
        } if destino else None),
        "lineas": [
            {"nombre": productos[int(linea.producto_id)].nombre if int(linea.producto_id) in productos else "",
             "cantidad": linea.cantidad}
            for linea in orden.orden.lineas
        ],
        "distancia_km": a_texto(orden.distancia_km),
        "ganancia": a_texto(orden.orden.envio),
        "aceptada_en": entrega.aceptada_en,
        "recogida_en": entrega.recogida_en,
        "entregada_en": entrega.entregada_en,
    }

def detalle(fabrica: FabricaUoW, repartidor: UsuarioActual, orden_id: int) -> dict:
    with fabrica() as uow:
        orden, entrega = _entrega_asignada(uow, repartidor, orden_id, bloquear=False)
        return _detalle(uow, orden, entrega)

def recoger(fabrica: FabricaUoW, repartidor: UsuarioActual, orden_id: int) -> dict:
    with fabrica() as uow:
        orden, entrega = _entrega_asignada(uow, repartidor, orden_id, bloquear=True)
        if entrega.estado != "ACEPTADA":
            raise Conflicto("La entrega ya fue recogida o completada", "ESTADO_ENTREGA_INVALIDO")
        if orden.orden.estado is EstadoOrden.PAGADA:
            raise Conflicto("La orden sigue pendiente de preparación", "ORDEN_PENDIENTE_PREPARACION")
        if orden.orden.estado is not EstadoOrden.EN_PREPARACION:
            raise Conflicto("La orden no está lista para recogerse", "TRANSICION_INVALIDA")

        ahora = datetime.now(timezone.utc)
        orden.orden.avanzar_estado(EstadoOrden.ENVIADA)
        uow.ordenes.guardar(orden)
        uow.eventos.agregar(EventoOrden(orden_id, EstadoOrden.ENVIADA.value, ahora, repartidor.id))
        entrega = replace(entrega, estado="RECOGIDA", recogida_en=ahora)
        uow.entregas.guardar(entrega)
        salida = _detalle(uow, orden, entrega)
        uow.commit()
        return salida

def entregar(fabrica: FabricaUoW, repartidor: UsuarioActual, orden_id: int, codigo: str) -> dict:
    with fabrica() as uow:
        orden, entrega = _entrega_asignada(uow, repartidor, orden_id, bloquear=True)
        if orden.codigo_entrega is None or codigo != orden.codigo_entrega:
            raise DatosInvalidos("El código de entrega no coincide", "CODIGO_ENTREGA_INVALIDO")
        if entrega.estado == "ENTREGADA" and orden.orden.estado is EstadoOrden.ENTREGADA:
            return _detalle(uow, orden, entrega)
        if entrega.estado != "RECOGIDA" or orden.orden.estado is not EstadoOrden.ENVIADA:
            raise Conflicto("La entrega no está en un estado que permita completarla", "ESTADO_ENTREGA_INVALIDO")

        ahora = datetime.now(timezone.utc)
        orden.orden.avanzar_estado(EstadoOrden.ENTREGADA)
        comprador = uow.usuarios.por_id(orden.comprador_id)
        if comprador is None:
            raise NoEncontrado("El comprador de la orden no existe")
        comprador.usuario.registrar_pedido_completado()
        uow.usuarios.guardar(comprador)
        uow.ordenes.guardar(orden)
        uow.eventos.agregar(EventoOrden(orden_id, EstadoOrden.ENTREGADA.value, ahora, repartidor.id))
        entrega = replace(entrega, estado="ENTREGADA", entregada_en=ahora)
        uow.entregas.guardar(entrega)
        salida = _detalle(uow, orden, entrega)
        uow.commit()
        return salida
