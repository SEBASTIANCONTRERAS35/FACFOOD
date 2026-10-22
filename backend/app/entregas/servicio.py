from datetime import datetime, timezone

from app.domain.erp.orden import EstadoOrden
from app.ports.repositorios import EntregaRegistro
from app.shared.auth import UsuarioActual
from app.shared.dinero import a_texto
from app.shared.errores import Conflicto, NoEncontrado
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
