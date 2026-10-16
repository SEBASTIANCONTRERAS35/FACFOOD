"""Rebanada Catálogo (Sebastián): puestos cercanos, menú y destinos. Vistas 02 y 03."""

from fastapi import APIRouter, Depends, Query

from app.catalogo import servicio
from app.catalogo.esquemas import ProductoSalida, PuntoVentaSalida
from app.shared.geo import FACULTAD_DE_INGENIERIA
from app.shared.uow import FabricaUoW, obtener_fabrica_uow

router = APIRouter(tags=["Catálogo"])

LAT, LON = FACULTAD_DE_INGENIERIA


@router.get("/puntos-venta", response_model=list[PuntoVentaSalida],
            summary="Puestos cercanos, del más cercano al más lejano (PostGIS)")
def puntos_cercanos(
    lat: float = Query(LAT, ge=-90, le=90),
    lon: float = Query(LON, ge=-180, le=180),
    radio: int = Query(1000, ge=50, le=5000, description="Metros"),
    categoria: str | None = Query(None, max_length=60),
    q: str | None = Query(None, max_length=60, description="Busca en nombre y categoría"),
    fabrica: FabricaUoW = Depends(obtener_fabrica_uow),
):
    return servicio.cercanos(fabrica, lat, lon, radio, categoria, q)


@router.get("/puntos-venta/categorias", response_model=list[str], summary="Categorías para los filtros")
def categorias(fabrica: FabricaUoW = Depends(obtener_fabrica_uow)):
    return servicio.categorias(fabrica)


@router.get("/puntos-venta/{punto_id}", response_model=PuntoVentaSalida, summary="Detalle del puesto")
def detalle(
    punto_id: int,
    lat: float | None = Query(None, ge=-90, le=90),
    lon: float | None = Query(None, ge=-180, le=180),
    fabrica: FabricaUoW = Depends(obtener_fabrica_uow),
):
    return servicio.detalle(fabrica, punto_id, lat, lon)


@router.get("/puntos-venta/{punto_id}/productos", response_model=list[ProductoSalida],
            summary="Menú del puesto (el precio lo dicta el servidor)")
def productos(punto_id: int, fabrica: FabricaUoW = Depends(obtener_fabrica_uow)):
    return servicio.productos(fabrica, punto_id)
