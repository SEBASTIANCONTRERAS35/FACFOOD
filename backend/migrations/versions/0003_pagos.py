"""Tabla de pagos: cada intento de cobro de una orden (ADR 004)

Revision ID: 0003_pagos
Revises: 0002_origen_descuento
Create Date: 2026-11-12
"""
import sqlalchemy as sa
from alembic import op

revision = "0003_pagos"
down_revision = "0002_origen_descuento"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "pagos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("orden_id", sa.Integer(), sa.ForeignKey("ordenes.id"), nullable=False),
        sa.Column("proveedor", sa.String(20), nullable=False),
        sa.Column("referencia", sa.String(255), nullable=True),
        sa.Column("monto", sa.Numeric(10, 2), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("expira_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evento_id", sa.String(255), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("estado IN ('PENDIENTE','PAGADO','FALLIDO','EXPIRADO')", name="ck_pagos_estado"),
        sa.CheckConstraint("monto > 0", name="ck_pagos_monto"),
        sa.UniqueConstraint("proveedor", "referencia", name="uq_pagos_referencia"),
    )
    op.create_index("ix_pagos_orden_id", "pagos", ["orden_id"])
    op.create_index(
        "uq_pagos_un_pendiente", "pagos", ["orden_id"], unique=True, postgresql_where=sa.text("estado = 'PENDIENTE'"),
    )


def downgrade():
    op.drop_index("uq_pagos_un_pendiente", table_name="pagos")
    op.drop_index("ix_pagos_orden_id", table_name="pagos")
    op.drop_table("pagos")
