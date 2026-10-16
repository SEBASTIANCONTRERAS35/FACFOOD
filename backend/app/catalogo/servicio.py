"""Casos de uso del catálogo: puestos cercanos (PostGIS) y detalle del puesto."""

from app.ports.repositorios import PuntoVenta
from app.shared.errores import NoEncontrado
from app.shared.uow import FabricaUoW


def a_salida(p: PuntoVenta, distancia_m: int | None) -> dict:
    return {
        "id": p.id, "nombre": p.nombre, "categoria": p.categoria, "descripcion": p.descripcion,
        "ubicacion_texto": p.ubicacion_texto, "lat": p.lat, "lon": p.lon, "distancia_m": distancia_m,
        "calificacion": float(p.calificacion), "num_resenas": p.num_resenas,
        "horario_cierre": p.horario_cierre, "abierto": p.abierto, "admite_entrega": p.admite_entrega,
    }


def cercanos(fabrica: FabricaUoW, lat: float, lon: float, radio_m: int,
             categoria: str | None, texto: str | None) -> list[dict]:
    with fabrica() as uow:
        encontrados = uow.puntos_venta.cercanos(lat, lon, radio_m, categoria or None, texto or None)
    # Primero los abiertos; dentro de cada grupo, el más cercano primero.
    encontrados.sort(key=lambda c: (not c.punto.abierto, c.distancia_m))
    return [a_salida(c.punto, c.distancia_m) for c in encontrados]


def categorias(fabrica: FabricaUoW) -> list[str]:
    with fabrica() as uow:
        return uow.puntos_venta.categorias()


def detalle(fabrica: FabricaUoW, punto_id: int, lat: float | None, lon: float | None) -> dict:
    with fabrica() as uow:
        punto = uow.puntos_venta.por_id(punto_id)
        if punto is None:
            raise NoEncontrado("Ese puesto no existe")
        distancia = uow.puntos_venta.distancia_m(punto_id, lat, lon) if lat is not None and lon is not None else None
    return a_salida(punto, distancia)
