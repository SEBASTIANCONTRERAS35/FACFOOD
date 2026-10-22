from datetime import datetime, timezone
from app.domain.erp.orden import EstadoOrden
from app.ports.repositorios import EventoOrden, UnidadDeTrabajo
from app.shared.auth import UsuarioActual
from app.shared.dinero import a_texto
from app.shared.errores import Conflicto, NoEncontrado
from app.shared.uow import FabricaUoW

def listar_ordenes(f: FabricaUoW, u: UsuarioActual):
    with f() as w:
        puntos = w.puntos_venta.de_vendedor(u.id)
        out = []
        for p in puntos:
            for r in w.ordenes.de_punto(p.id):
                if r.orden.estado in (EstadoOrden.PAGADA, EstadoOrden.EN_PREPARACION):
                    out.append({
                        "id": r.id, "estado": r.orden.estado.value,
                        "punto_venta_id": p.id, "punto_venta": p.nombre,
                        "metodo_entrega": r.metodo_entrega,
                        "total": a_texto(r.orden.total),
                        "creada_en": r.creada_en.isoformat() if r.creada_en else None,
                    })
        return {
            "ordenes": out,
            "puntos_venta": [{"id": p.id, "nombre": p.nombre, "abierto": p.abierto} for p in puntos],
        }

def _propia(w: UnidadDeTrabajo, u: UsuarioActual, i: int):
    r = w.ordenes.por_id(i, bloquear=True)
    if not r:
        raise NoEncontrado("La orden no existe")
    p = w.puntos_venta.por_id(r.punto_venta_id)
    if not p or p.vendedor_id != u.id:
        raise NoEncontrado("La orden no existe")
    return r

def cambiar_estado(f: FabricaUoW, u: UsuarioActual, i: int, estado: str):
    with f() as w:
        r = _propia(w, u, i)
        if estado == EstadoOrden.ENVIADA.value and r.metodo_entrega == "estudiante":
            raise Conflicto("La entrega estudiantil debe marcarla el repartidor", "TRANSICION_NO_AUTORIZADA")
        r.orden.avanzar_estado(estado)
        w.ordenes.guardar(r)
        w.eventos.agregar(EventoOrden(i, r.orden.estado.value, datetime.now(timezone.utc), u.id))
        w.commit()
        return {"id": i, "estado": r.orden.estado.value}

def cambiar_punto(f: FabricaUoW, u: UsuarioActual, i: int, abierto: bool):
    with f() as w:
        p = w.puntos_venta.por_id(i)
        if not p or p.vendedor_id != u.id:
            raise NoEncontrado("El puesto no existe")
        w.puntos_venta.cambiar_abierto(i, abierto)
        w.commit()
        return {"id": p.id, "nombre": p.nombre, "abierto": abierto}
