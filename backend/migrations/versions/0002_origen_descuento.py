"""Guardar de dónde salió el descuento de la orden (cupón o lealtad)

Revision ID: 0002_origen_descuento
Revises: 0001_esquema_base
Create Date: 2026-10-16
"""
import sqlalchemy as sa
from alembic import op

revision = "0002_origen_descuento"
down_revision = "0001_esquema_base"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("ordenes", sa.Column("origen_descuento", sa.String(10), nullable=True))
    op.create_check_constraint(
        "ck_ordenes_origen_descuento", "ordenes", "origen_descuento IN ('cupon','lealtad')"
    )


def downgrade():
    op.drop_constraint("ck_ordenes_origen_descuento", "ordenes", type_="check")
    op.drop_column("ordenes", "origen_descuento")
