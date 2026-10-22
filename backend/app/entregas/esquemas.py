from pydantic import BaseModel

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
