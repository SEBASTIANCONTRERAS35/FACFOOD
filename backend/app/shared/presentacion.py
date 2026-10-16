"""Objeto Orden en JSON (docs/CONTRATO.md §6). Lo usan checkout (vista 04) y seguimiento (vista 05)."""

from app.ports.repositorios import OrdenRegistro, UnidadDeTrabajo
from app.shared.dinero import a_texto


def orden_a_json(uow: UnidadDeTrabajo, r: OrdenRegistro, usuario_id: int | None = None) -> dict:
    """`usuario_id` es quien pregunta: el código de entrega solo se le muestra al comprador."""
    o = r.orden
    punto = uow.puntos_venta.por_id(r.punto_venta_id)
    productos = {p.id: p for p in uow.productos.de_punto(r.punto_venta_id)}
    destino = uow.destinos.por_id(r.destino_id) if r.destino_id else None
    cupon = uow.cupones.por_id(r.cupon_id) if r.cupon_id else None
    factura = uow.facturas.de_orden(r.id) if r.id else None
    return {
        "id": r.id,
        "estado": o.estado.value,
        "comprador_id": r.comprador_id,
        "punto_venta": {"id": punto.id, "nombre": punto.nombre},
        "lineas": [
            {
                "producto_id": int(l.producto_id),
                "nombre": productos[int(l.producto_id)].nombre if int(l.producto_id) in productos else "",
                "cantidad": l.cantidad,
                "precio_unitario": a_texto(l.precio_unitario),
                "importe": a_texto(l.subtotal),
            }
            for l in o.lineas
        ],
        "metodo_entrega": r.metodo_entrega,
        "destino": {"id": destino.id, "nombre": destino.nombre} if destino else None,
        "distancia_km": a_texto(r.distancia_km),
        "subtotal": a_texto(o.subtotal),
        "descuento": a_texto(o.descuentos),
        "origen_descuento": o.origen_descuento,
        "cupon": cupon.cupon.codigo if cupon else None,
        "iva": a_texto(o.iva),
        "envio": a_texto(o.envio),
        "total": a_texto(o.total),
        "codigo_entrega": r.codigo_entrega if usuario_id == r.comprador_id else None,
        "factura_folio": str(factura.factura.folio_fiscal) if factura else None,
        "creada_en": r.creada_en.isoformat() if r.creada_en else None,
    }
