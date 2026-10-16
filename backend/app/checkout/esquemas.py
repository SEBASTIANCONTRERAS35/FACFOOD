from typing import Literal

from pydantic import BaseModel, Field


class LineaEntrada(BaseModel):
    producto_id: int
    cantidad: int = Field(gt=0, le=50)


class CrearOrdenEntrada(BaseModel):
    """El cliente solo manda IDs y cantidades: el precio lo dicta el servidor."""

    punto_venta_id: int
    lineas: list[LineaEntrada] = Field(min_length=1, max_length=30)
    metodo_entrega: Literal["pickup", "estudiante"] = "pickup"
    destino_id: int | None = None


class EntregaEntrada(BaseModel):
    metodo_entrega: Literal["pickup", "estudiante"]
    destino_id: int | None = None


class CuponEntrada(BaseModel):
    codigo: str = Field(min_length=1, max_length=40)


class PagoEntrada(BaseModel):
    rfc: str | None = Field(default=None, max_length=13, description="Opcional; si no, público en general")


class Ref(BaseModel):
    id: int
    nombre: str


class LineaSalida(BaseModel):
    producto_id: int
    nombre: str
    cantidad: int
    precio_unitario: str
    importe: str


class OrdenSalida(BaseModel):
    id: int
    estado: str
    comprador_id: int
    punto_venta: Ref
    lineas: list[LineaSalida]
    metodo_entrega: str
    destino: Ref | None
    distancia_km: str
    subtotal: str
    descuento: str
    origen_descuento: str | None
    cupon: str | None
    iva: str
    envio: str
    total: str
    codigo_entrega: str | None
    factura_folio: str | None
    creada_en: str | None
