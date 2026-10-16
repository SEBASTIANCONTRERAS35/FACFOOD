"""Tablas de PostgreSQL (SQLAlchemy 2). El esquema se crea con Alembic (migrations/).

Dueños de escritura (ver docs/CONTRATO.md):
  Sebastián: usuarios, puntos_venta, productos, destinos, cupones, usos_cupon,
             ordenes (crear/pagar), lineas_orden, facturas
  Arturo:    entregas; ordenes de PAGADA en adelante y puntos_venta.abierto
  Ambos:     orden_eventos (cada quien registra las transiciones de su tramo)
"""

from datetime import date, datetime
from decimal import Decimal

from geoalchemy2 import Geography
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def es_nuestro(objeto, nombre, tipo, reflejado, comparado_con) -> bool:
    """Filtro para Alembic: ignora lo que crean PostGIS y su geocodificador (tiger, etc.)."""
    if tipo == "table":
        return nombre in Base.metadata.tables
    tabla = getattr(objeto, "table", None)
    return tabla is None or tabla.name in Base.metadata.tables


def _punto():
    return Geography(geometry_type="POINT", srid=4326, spatial_index=False)


class UsuarioM(Base):
    __tablename__ = "usuarios"
    id: Mapped[int] = mapped_column(primary_key=True)
    correo: Mapped[str] = mapped_column(String(254), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    credencial_unam: Mapped[str] = mapped_column(String(20), unique=True)
    password_hash: Mapped[bytes | None] = mapped_column(LargeBinary)
    consentimiento_datos: Mapped[bool] = mapped_column(Boolean)
    rol: Mapped[str] = mapped_column(String(20), default="comprador")
    pedidos_completados: Mapped[int] = mapped_column(Integer, default=0)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint("consentimiento_datos", name="ck_usuarios_consentimiento"),
        CheckConstraint("rol IN ('comprador','vendedor','repartidor')", name="ck_usuarios_rol"),
    )


class PuntoVentaM(Base):
    __tablename__ = "puntos_venta"
    id: Mapped[int] = mapped_column(primary_key=True)
    vendedor_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    nombre: Mapped[str] = mapped_column(String(120))
    categoria: Mapped[str] = mapped_column(String(60))
    descripcion: Mapped[str] = mapped_column(Text, default="")
    ubicacion_texto: Mapped[str] = mapped_column(String(200), default="")
    ubicacion = mapped_column(_punto(), nullable=False)
    calificacion: Mapped[Decimal] = mapped_column(Numeric(2, 1), default=0)
    num_resenas: Mapped[int] = mapped_column(Integer, default=0)
    horario_cierre: Mapped[str] = mapped_column(String(5), default="18:00")
    abierto: Mapped[bool] = mapped_column(Boolean, default=True)
    admite_entrega: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (Index("ix_puntos_venta_ubicacion", "ubicacion", postgresql_using="gist"),)


class ProductoM(Base):
    __tablename__ = "productos"
    id: Mapped[int] = mapped_column(primary_key=True)
    punto_venta_id: Mapped[int] = mapped_column(ForeignKey("puntos_venta.id"), index=True)
    nombre: Mapped[str] = mapped_column(String(120))
    descripcion: Mapped[str] = mapped_column(Text, default="")
    precio: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    disponible: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (CheckConstraint("precio > 0", name="ck_productos_precio"),)


class DestinoM(Base):
    __tablename__ = "destinos"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True)
    ubicacion = mapped_column(_punto(), nullable=False)


class CuponM(Base):
    __tablename__ = "cupones"
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(40), unique=True)
    porcentaje: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    vigente_hasta: Mapped[date] = mapped_column(Date)
    pedido_minimo: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    tope_descuento: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    usos_maximos: Mapped[int] = mapped_column(Integer, default=1)
    usos_actuales: Mapped[int] = mapped_column(Integer, default=0)
    solo_primer_pedido: Mapped[bool] = mapped_column(Boolean, default=False)
    uno_por_usuario: Mapped[bool] = mapped_column(Boolean, default=False)
    __table_args__ = (CheckConstraint("usos_actuales <= usos_maximos", name="ck_cupones_usos"),)


class OrdenM(Base):
    __tablename__ = "ordenes"
    id: Mapped[int] = mapped_column(primary_key=True)
    comprador_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    punto_venta_id: Mapped[int] = mapped_column(ForeignKey("puntos_venta.id"), index=True)
    estado: Mapped[str] = mapped_column(String(20), index=True)
    fecha: Mapped[date] = mapped_column(Date)
    metodo_entrega: Mapped[str] = mapped_column(String(20))
    destino_id: Mapped[int | None] = mapped_column(ForeignKey("destinos.id"))
    distancia_km: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    cupon_id: Mapped[int | None] = mapped_column(ForeignKey("cupones.id"))
    pedidos_completados_al_crear: Mapped[int] = mapped_column(Integer, default=0)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    descuento: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    iva: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    envio: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    codigo_entrega: Mapped[str | None] = mapped_column(String(4))
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint(
            "estado IN ('CREADA','PAGADA','EN_PREPARACION','ENVIADA','ENTREGADA','CANCELADA')",
            name="ck_ordenes_estado",
        ),
        CheckConstraint("metodo_entrega IN ('pickup','estudiante')", name="ck_ordenes_metodo"),
    )


class LineaOrdenM(Base):
    __tablename__ = "lineas_orden"
    id: Mapped[int] = mapped_column(primary_key=True)
    orden_id: Mapped[int] = mapped_column(ForeignKey("ordenes.id", ondelete="CASCADE"), index=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"))
    cantidad: Mapped[int] = mapped_column(Integer)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    __table_args__ = (CheckConstraint("cantidad > 0", name="ck_lineas_cantidad"),)


class UsoCuponM(Base):
    __tablename__ = "usos_cupon"
    id: Mapped[int] = mapped_column(primary_key=True)
    cupon_id: Mapped[int] = mapped_column(ForeignKey("cupones.id"), index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    orden_id: Mapped[int] = mapped_column(ForeignKey("ordenes.id"), unique=True)
    usado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EventoOrdenM(Base):
    __tablename__ = "orden_eventos"
    id: Mapped[int] = mapped_column(primary_key=True)
    orden_id: Mapped[int] = mapped_column(ForeignKey("ordenes.id", ondelete="CASCADE"), index=True)
    estado: Mapped[str] = mapped_column(String(20))
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FacturaM(Base):
    __tablename__ = "facturas"
    folio_fiscal = mapped_column(Uuid, primary_key=True)
    orden_id: Mapped[int] = mapped_column(ForeignKey("ordenes.id"), unique=True)
    rfc_receptor: Mapped[str] = mapped_column(String(13))
    xml: Mapped[str] = mapped_column(Text)
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EntregaM(Base):
    """Rebanada de Arturo (vistas 07-08). Se crea aquí para que el esquema exista desde el día 1."""

    __tablename__ = "entregas"
    id: Mapped[int] = mapped_column(primary_key=True)
    orden_id: Mapped[int] = mapped_column(ForeignKey("ordenes.id"), unique=True)
    repartidor_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    estado: Mapped[str] = mapped_column(String(20), default="ACEPTADA")
    aceptada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    recogida_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    entregada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint("estado IN ('ACEPTADA','RECOGIDA','ENTREGADA')", name="ck_entregas_estado"),
    )
