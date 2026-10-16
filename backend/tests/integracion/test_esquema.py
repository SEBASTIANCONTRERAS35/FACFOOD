from decimal import Decimal

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext

from app.adapters.postgres.modelos import Base
from app.domain.erp.orden import EstadoOrden


def test_la_migracion_coincide_con_los_modelos(sesiones):
    with sesiones() as s:
        contexto = MigrationContext.configure(
            s.connection(),
            opts={"include_object": lambda o, n, t, r, c: not (t == "table" and n == "spatial_ref_sys")},
        )
        diferencias = compare_metadata(contexto, Base.metadata)
    assert diferencias == []


def test_puestos_cercanos_ordenados_por_distancia_con_postgis(fabrica_pg):
    with fabrica_pg() as uow:
        cercanos = uow.puntos_venta.cercanos(19.3311, -99.1839, 500)
        lejos = uow.puntos_venta.cercanos(19.3311, -99.1839, 100)
    distancias = [c.distancia_m for c in cercanos]
    assert distancias == sorted(distancias)
    assert {c.punto.nombre for c in cercanos} >= {"Tacos Don Memo", "Café Ingeniería"}
    assert lejos == []


def test_la_orden_de_ejemplo_se_restaura_igual_que_se_guardo(fabrica_pg):
    with fabrica_pg() as uow:
        registro = uow.ordenes.por_id(1)
        eventos = uow.eventos.de_orden(1)
        factura = uow.facturas.de_orden(1)
    assert registro.orden.estado is EstadoOrden.PAGADA
    assert registro.metodo_entrega == "estudiante"
    assert registro.orden.subtotal == Decimal("69.00")
    assert registro.orden.total == registro.orden.subtotal + registro.orden.iva + registro.orden.envio
    assert [e.estado for e in eventos] == ["CREADA", "PAGADA"]
    assert factura is not None and b"XAXX010101000" in factura.factura.xml_data
