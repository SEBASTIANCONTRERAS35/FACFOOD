from datetime import datetime

from pydantic import BaseModel, Field

class LineaEntregaDisponible(BaseModel):
    nombre: str
    cantidad: int

class EntregaDisponibleSalida(BaseModel):
    orden_id: int
    estado: str
    puesto: str
    lugar_recogida: str
    destino: str | None
    lineas: list[LineaEntregaDisponible]
    distancia_km: str
    ganancia: str

class ListaEntregasDisponibles(BaseModel):
    entregas: list[EntregaDisponibleSalida]

class EntregaAceptadaSalida(BaseModel):
    orden_id: int
    estado: str

class CoordenadasSalida(BaseModel):
    lat: float
    lon: float

class PuntoEntregaSalida(CoordenadasSalida):
    nombre: str
    ubicacion: str

class DestinoEntregaSalida(CoordenadasSalida):
    nombre: str

class EntregaDetalleSalida(BaseModel):
    orden_id: int
    estado_orden: str
    estado_entrega: str
    puesto: PuntoEntregaSalida
    destino: DestinoEntregaSalida | None
    lineas: list[LineaEntregaDisponible]
    distancia_km: str
    ganancia: str
    aceptada_en: datetime | None
    recogida_en: datetime | None
    entregada_en: datetime | None

class CodigoEntregaEntrada(BaseModel):
    codigo_entrega: str = Field(pattern=r"^[0-9]{4}$", strict=True)
