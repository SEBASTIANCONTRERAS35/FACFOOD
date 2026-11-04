"""DTOs del checkout. Los de entrada validan con Pydantic (400 si no cumplen); los de salida
deciden qué se expone: nunca precios que mande el cliente ni datos de otros usuarios."""

from typing import Literal

from pydantic import BaseModel, Field


class LineaEntrada(BaseModel):
    producto_id: int = Field(description="ID del producto en el menú del puesto", examples=[1])
    cantidad: int = Field(gt=0, le=50, description="Piezas, de 1 a 50", examples=[2])


class CrearOrdenEntrada(BaseModel):
    """El cliente solo manda IDs y cantidades: el precio lo dicta el servidor (nunca confiar en el frontend)."""

    punto_venta_id: int = Field(description="Puesto al que se le pide", examples=[1])
    lineas: list[LineaEntrada] = Field(min_length=1, max_length=30, description="De 1 a 30 líneas")
    metodo_entrega: Literal["pickup", "estudiante"] = Field(
        "pickup", description="`pickup`: lo recoges, $0 · `estudiante`: te lo lleva un estudiante, $5 por km"
    )
    destino_id: int | None = Field(
        None, description="Obligatorio con `estudiante`: facultad o edificio de entrega (`GET /destinos`)"
    )


class EntregaEntrada(BaseModel):
    metodo_entrega: Literal["pickup", "estudiante"]
    destino_id: int | None = None


class CuponEntrada(BaseModel):
    codigo: str = Field(min_length=1, max_length=40, description="No distingue mayúsculas", examples=["BIENVENIDA15"])


class PagoEntrada(BaseModel):
    rfc: str | None = Field(
        default=None, max_length=13, description="RFC para la factura; si se omite, público en general (XAXX010101000)",
    )


class Ref(BaseModel):
    id: int
    nombre: str


class LineaSalida(BaseModel):
    producto_id: int
    nombre: str
    cantidad: int
    precio_unitario: str = Field(description="Precio del catálogo al momento de pedir")
    importe: str


class OrdenSalida(BaseModel):
    """Orden según docs/CONTRATO.md §6. Dinero como texto con 2 decimales."""

    id: int
    estado: str = Field(description="CREADA → PAGADA → EN_PREPARACION → ENVIADA → ENTREGADA (o CANCELADA)")
    comprador_id: int
    punto_venta: Ref
    lineas: list[LineaSalida]
    metodo_entrega: str
    destino: Ref | None
    distancia_km: str
    subtotal: str
    descuento: str = Field(description="El mayor entre cupón y lealtad; nunca se suman")
    origen_descuento: str | None = Field(description="`cupon`, `lealtad` o null")
    cupon: str | None
    iva: str = Field(description="16% sobre (subtotal − descuento)")
    envio: str
    total: str = Field(description="(subtotal − descuento) + IVA + envío")
    codigo_entrega: str | None = Field(
        description="Dato sensible: solo se envía al comprador de la orden y solo en entrega estudiante ya pagada"
    )
    factura_folio: str | None
    creada_en: str | None


class OrdenResumen(BaseModel):
    """Un pedido en la lista de "Mis pedidos". El detalle completo está en GET /ordenes/{id}."""

    id: int
    estado: str
    punto_venta: Ref
    metodo_entrega: str
    piezas: int = Field(description="Total de productos del pedido")
    total: str
    creada_en: str | None


EJEMPLO_ORDEN = {
    "id": 5, "estado": "CREADA", "comprador_id": 1,
    "punto_venta": {"id": 1, "nombre": "Tacos Don Memo"},
    "lineas": [
        {"producto_id": 1, "nombre": "Taco de pastor", "cantidad": 2, "precio_unitario": "18.00", "importe": "36.00"},
        {"producto_id": 3, "nombre": "Quesadilla de queso", "cantidad": 1, "precio_unitario": "30.00", "importe": "30.00"},
    ],
    "metodo_entrega": "pickup", "destino": None, "distancia_km": "0.00",
    "subtotal": "66.00", "descuento": "0.00", "origen_descuento": None, "cupon": None,
    "iva": "10.56", "envio": "0.00", "total": "76.56",
    "codigo_entrega": None, "factura_folio": None, "creada_en": "2026-11-05T19:02:00+00:00",
}
