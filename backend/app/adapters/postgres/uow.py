from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.adapters.postgres.repos import (
    CuponRepoPg,
    DestinoRepoPg,
    EntregaRepoPg,
    EventoRepoPg,
    FacturaRepoPg,
    OrdenRepoPg,
    ProductoRepoPg,
    PuntoVentaRepoPg,
    UsuarioRepoPg,
)


def crear_fabrica_sesiones(database_url: str) -> sessionmaker:
    motor = create_engine(database_url, pool_pre_ping=True)
    return sessionmaker(bind=motor, expire_on_commit=False)


class UnidadDeTrabajoPostgres:
    """Una transacción de base de datos; sin commit() todo se revierte."""

    def __init__(self, fabrica_sesiones: sessionmaker):
        self._fabrica = fabrica_sesiones

    def __enter__(self):
        self.sesion = self._fabrica()
        s = self.sesion
        self.usuarios = UsuarioRepoPg(s)
        self.puntos_venta = PuntoVentaRepoPg(s)
        self.productos = ProductoRepoPg(s)
        self.destinos = DestinoRepoPg(s)
        self.cupones = CuponRepoPg(s)
        self.ordenes = OrdenRepoPg(s)
        self.eventos = EventoRepoPg(s)
        self.facturas = FacturaRepoPg(s)
        self.entregas = EntregaRepoPg(s)
        return self

    def __exit__(self, *exc):
        self.sesion.rollback()  # no hace nada si ya hubo commit()
        self.sesion.close()

    def commit(self):
        self.sesion.commit()
