"""Esquema base de FACFOOD (todas las tablas del MVP)

Revision ID: 0001_esquema_base
Revises:
Create Date: 2026-10-16
"""
import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geography

revision = "0001_esquema_base"
down_revision = None
branch_labels = None
depends_on = None


def _punto():
    return Geography(geometry_type="POINT", srid=4326, spatial_index=False)


def _ahora():
    return sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("correo", sa.String(254), nullable=False, unique=True),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("credencial_unam", sa.String(20), nullable=False, unique=True),
        sa.Column("password_hash", sa.LargeBinary, nullable=True),
        sa.Column("consentimiento_datos", sa.Boolean, nullable=False),
        sa.Column("rol", sa.String(20), nullable=False),
        sa.Column("pedidos_completados", sa.Integer, nullable=False),
        _ahora(),
        sa.CheckConstraint("consentimiento_datos", name="ck_usuarios_consentimiento"),
        sa.CheckConstraint("rol IN ('comprador','vendedor','repartidor')", name="ck_usuarios_rol"),
    )

    op.create_table(
        "puntos_venta",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("vendedor_id", sa.Integer, sa.ForeignKey("usuarios.id"), nullable=True),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("categoria", sa.String(60), nullable=False),
        sa.Column("descripcion", sa.Text, nullable=False),
        sa.Column("ubicacion_texto", sa.String(200), nullable=False),
        sa.Column("ubicacion", _punto(), nullable=False),
        sa.Column("calificacion", sa.Numeric(2, 1), nullable=False),
        sa.Column("num_resenas", sa.Integer, nullable=False),
        sa.Column("horario_cierre", sa.String(5), nullable=False),
        sa.Column("abierto", sa.Boolean, nullable=False),
        sa.Column("admite_entrega", sa.Boolean, nullable=False),
    )
    op.create_index("ix_puntos_venta_ubicacion", "puntos_venta", ["ubicacion"], postgresql_using="gist")

    op.create_table(
        "productos",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("punto_venta_id", sa.Integer, sa.ForeignKey("puntos_venta.id"), nullable=False),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("descripcion", sa.Text, nullable=False),
        sa.Column("precio", sa.Numeric(10, 2), nullable=False),
        sa.Column("disponible", sa.Boolean, nullable=False),
        sa.CheckConstraint("precio > 0", name="ck_productos_precio"),
    )
    op.create_index("ix_productos_punto_venta_id", "productos", ["punto_venta_id"])

    op.create_table(
        "destinos",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nombre", sa.String(120), nullable=False, unique=True),
        sa.Column("ubicacion", _punto(), nullable=False),
    )

    op.create_table(
        "cupones",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("codigo", sa.String(40), nullable=False, unique=True),
        sa.Column("porcentaje", sa.Numeric(5, 2), nullable=False),
        sa.Column("vigente_hasta", sa.Date, nullable=False),
        sa.Column("pedido_minimo", sa.Numeric(10, 2), nullable=False),
        sa.Column("tope_descuento", sa.Numeric(10, 2), nullable=True),
        sa.Column("usos_maximos", sa.Integer, nullable=False),
        sa.Column("usos_actuales", sa.Integer, nullable=False),
        sa.Column("solo_primer_pedido", sa.Boolean, nullable=False),
        sa.Column("uno_por_usuario", sa.Boolean, nullable=False),
        sa.CheckConstraint("usos_actuales <= usos_maximos", name="ck_cupones_usos"),
    )

    op.create_table(
        "ordenes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("comprador_id", sa.Integer, sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("punto_venta_id", sa.Integer, sa.ForeignKey("puntos_venta.id"), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("fecha", sa.Date, nullable=False),
        sa.Column("metodo_entrega", sa.String(20), nullable=False),
        sa.Column("destino_id", sa.Integer, sa.ForeignKey("destinos.id"), nullable=True),
        sa.Column("distancia_km", sa.Numeric(6, 2), nullable=False),
        sa.Column("cupon_id", sa.Integer, sa.ForeignKey("cupones.id"), nullable=True),
        sa.Column("pedidos_completados_al_crear", sa.Integer, nullable=False),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False),
        sa.Column("descuento", sa.Numeric(10, 2), nullable=False),
        sa.Column("iva", sa.Numeric(10, 2), nullable=False),
        sa.Column("envio", sa.Numeric(10, 2), nullable=False),
        sa.Column("total", sa.Numeric(10, 2), nullable=False),
        sa.Column("codigo_entrega", sa.String(4), nullable=True),
        sa.Column("creada_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "estado IN ('CREADA','PAGADA','EN_PREPARACION','ENVIADA','ENTREGADA','CANCELADA')",
            name="ck_ordenes_estado",
        ),
        sa.CheckConstraint("metodo_entrega IN ('pickup','estudiante')", name="ck_ordenes_metodo"),
    )
    op.create_index("ix_ordenes_comprador_id", "ordenes", ["comprador_id"])
    op.create_index("ix_ordenes_punto_venta_id", "ordenes", ["punto_venta_id"])
    op.create_index("ix_ordenes_estado", "ordenes", ["estado"])

    op.create_table(
        "lineas_orden",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("orden_id", sa.Integer, sa.ForeignKey("ordenes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("producto_id", sa.Integer, sa.ForeignKey("productos.id"), nullable=False),
        sa.Column("cantidad", sa.Integer, nullable=False),
        sa.Column("precio_unitario", sa.Numeric(10, 2), nullable=False),
        sa.CheckConstraint("cantidad > 0", name="ck_lineas_cantidad"),
    )
    op.create_index("ix_lineas_orden_orden_id", "lineas_orden", ["orden_id"])

    op.create_table(
        "usos_cupon",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("cupon_id", sa.Integer, sa.ForeignKey("cupones.id"), nullable=False),
        sa.Column("usuario_id", sa.Integer, sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("orden_id", sa.Integer, sa.ForeignKey("ordenes.id"), nullable=False, unique=True),
        sa.Column("usado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_usos_cupon_cupon_id", "usos_cupon", ["cupon_id"])

    op.create_table(
        "orden_eventos",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("orden_id", sa.Integer, sa.ForeignKey("ordenes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("actor_id", sa.Integer, sa.ForeignKey("usuarios.id"), nullable=True),
        _ahora(),
    )
    op.create_index("ix_orden_eventos_orden_id", "orden_eventos", ["orden_id"])

    op.create_table(
        "facturas",
        sa.Column("folio_fiscal", sa.Uuid, primary_key=True),
        sa.Column("orden_id", sa.Integer, sa.ForeignKey("ordenes.id"), nullable=False, unique=True),
        sa.Column("rfc_receptor", sa.String(13), nullable=False),
        sa.Column("xml", sa.Text, nullable=False),
        sa.Column("creada_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "entregas",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("orden_id", sa.Integer, sa.ForeignKey("ordenes.id"), nullable=False, unique=True),
        sa.Column("repartidor_id", sa.Integer, sa.ForeignKey("usuarios.id"), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("aceptada_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recogida_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("entregada_en", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("estado IN ('ACEPTADA','RECOGIDA','ENTREGADA')", name="ck_entregas_estado"),
    )


def downgrade():
    for tabla in ["entregas", "facturas", "orden_eventos", "usos_cupon", "lineas_orden",
                  "ordenes", "cupones", "destinos", "productos", "puntos_venta", "usuarios"]:
        op.drop_table(tabla)
