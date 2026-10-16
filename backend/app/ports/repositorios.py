"""Puertos (interfaces) de persistencia — arquitectura hexagonal.

Los servicios de cada rebanada (cuentas, catalogo, checkout, seguimiento,
vendedor, entregas) solo conocen estas interfaces. Hay dos adaptadores:
  - app/adapters/memoria: datos de ejemplo en memoria (pruebas y desarrollo sin BD)
  - app/adapters/postgres: PostgreSQL + PostGIS

Ver docs/CONTRATO.md para quién escribe en cada tabla.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol

from app.domain.crm.retencion import Cupon
from app.domain.erp.factura import Factura
from app.domain.erp.orden import Orden
from app.domain.usuario import Usuario

ROLES = ("comprador", "vendedor", "repartidor")
METODOS_ENTREGA = ("pickup", "estudiante")


# ---- Registros (lo que se guarda, envolviendo a las entidades de dominio) ----
@dataclass
class CuentaUsuario:
    id: int | None
    correo: str
    usuario: Usuario
    creado_en: datetime | None = None


@dataclass(frozen=True)
class PuntoVenta:
    id: int
    vendedor_id: int | None
    nombre: str
    categoria: str
    descripcion: str
    ubicacion_texto: str
    lat: float
    lon: float
    calificacion: Decimal
    num_resenas: int
    horario_cierre: str  # "HH:MM"
    abierto: bool
    admite_entrega: bool


@dataclass(frozen=True)
class PuntoVentaCercano:
    punto: PuntoVenta
    distancia_m: int


@dataclass(frozen=True)
class Producto:
    id: int
    punto_venta_id: int
    nombre: str
    descripcion: str
    precio: Decimal
    disponible: bool


@dataclass(frozen=True)
class Destino:
    id: int
    nombre: str
    lat: float
    lon: float


@dataclass
class CuponRegistro:
    id: int | None
    cupon: Cupon
    solo_primer_pedido: bool = False
    uno_por_usuario: bool = False


@dataclass
class OrdenRegistro:
    id: int | None
    comprador_id: int
    punto_venta_id: int
    orden: Orden
    metodo_entrega: str  # "pickup" | "estudiante"
    destino_id: int | None = None
    distancia_km: Decimal = Decimal("0")
    cupon_id: int | None = None
    pedidos_completados_al_crear: int = 0
    codigo_entrega: str | None = None
    creada_en: datetime | None = None


@dataclass(frozen=True)
class EventoOrden:
    orden_id: int
    estado: str
    creado_en: datetime
    actor_id: int | None = None


@dataclass(frozen=True)
class FacturaRegistro:
    orden_id: int
    factura: Factura
    creada_en: datetime


# ---- Puertos ----
class UsuarioRepo(Protocol):
    def agregar(self, cuenta: CuentaUsuario) -> CuentaUsuario: ...
    def guardar(self, cuenta: CuentaUsuario) -> None: ...
    def por_id(self, usuario_id: int) -> CuentaUsuario | None: ...
    def por_correo(self, correo: str) -> CuentaUsuario | None: ...
    def existe_credencial(self, credencial_unam: str) -> bool: ...
    def listar(self) -> list[CuentaUsuario]: ...


class PuntoVentaRepo(Protocol):
    def agregar(self, punto: PuntoVenta) -> PuntoVenta: ...
    def por_id(self, punto_id: int) -> PuntoVenta | None: ...
    def cercanos(
        self, lat: float, lon: float, radio_m: int,
        categoria: str | None = None, texto: str | None = None,
    ) -> list[PuntoVentaCercano]: ...
    def distancia_m(self, punto_id: int, lat: float, lon: float) -> int: ...
    def categorias(self) -> list[str]: ...
    def cambiar_abierto(self, punto_id: int, abierto: bool) -> None: ...


class ProductoRepo(Protocol):
    def agregar(self, producto: Producto) -> Producto: ...
    def de_punto(self, punto_id: int) -> list[Producto]: ...


class DestinoRepo(Protocol):
    def agregar(self, destino: Destino) -> Destino: ...
    def listar(self) -> list[Destino]: ...
    def por_id(self, destino_id: int) -> Destino | None: ...


class CuponRepo(Protocol):
    def agregar(self, registro: CuponRegistro) -> CuponRegistro: ...
    def guardar(self, registro: CuponRegistro) -> None: ...
    def por_id(self, cupon_id: int, bloquear: bool = False) -> CuponRegistro | None: ...
    def por_codigo(self, codigo: str) -> CuponRegistro | None: ...
    def usos_de_usuario(self, cupon_id: int, usuario_id: int) -> int: ...
    def registrar_uso(self, cupon_id: int, usuario_id: int, orden_id: int) -> None: ...


class OrdenRepo(Protocol):
    def agregar(self, registro: OrdenRegistro) -> OrdenRegistro: ...
    def guardar(self, registro: OrdenRegistro) -> None: ...
    def por_id(self, orden_id: int, bloquear: bool = False) -> OrdenRegistro | None: ...
    def de_punto(self, punto_id: int) -> list[OrdenRegistro]: ...


class EventoRepo(Protocol):
    def agregar(self, evento: EventoOrden) -> None: ...
    def de_orden(self, orden_id: int) -> list[EventoOrden]: ...


class FacturaRepo(Protocol):
    def agregar(self, registro: FacturaRegistro) -> None: ...
    def de_orden(self, orden_id: int) -> FacturaRegistro | None: ...


class UnidadDeTrabajo(Protocol):
    """Una transacción: todo lo hecho dentro se confirma con commit() o se descarta."""

    usuarios: UsuarioRepo
    puntos_venta: PuntoVentaRepo
    productos: ProductoRepo
    destinos: DestinoRepo
    cupones: CuponRepo
    ordenes: OrdenRepo
    eventos: EventoRepo
    facturas: FacturaRepo

    def __enter__(self) -> "UnidadDeTrabajo": ...
    def __exit__(self, *exc) -> None: ...
    def commit(self) -> None: ...
