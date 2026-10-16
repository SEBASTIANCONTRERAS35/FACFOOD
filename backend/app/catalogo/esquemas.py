from pydantic import BaseModel


class PuntoVentaSalida(BaseModel):
    id: int
    nombre: str
    categoria: str
    descripcion: str
    ubicacion_texto: str
    lat: float
    lon: float
    distancia_m: int | None
    calificacion: float
    num_resenas: int
    horario_cierre: str
    abierto: bool
    admite_entrega: bool
