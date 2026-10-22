from datetime import datetime, timezone

import pytest

from app.domain.erp.orden import EstadoOrden
from app.ports.repositorios import EntregaRegistro
from app.shared.auth import UsuarioActual
from app.shared.errores import DatosInvalidos
from app.adapters.memoria.uow import EntregaRepoMemoria
from app.entregas.servicio import entregar

def preparar(fabrica):
    with fabrica() as uow:
        orden = uow.ordenes.por_id(1)
        orden.orden.avanzar_estado(EstadoOrden.EN_PREPARACION)
        orden.orden.avanzar_estado(EstadoOrden.ENVIADA)
        uow.ordenes.guardar(orden)
        uow.entregas.agregar(EntregaRegistro(
            None, 1, 5, "RECOGIDA", datetime.now(timezone.utc), datetime.now(timezone.utc),
        ))
        uow.commit()

def test_error_de_codigo_no_confirma_nada(fabrica):
    preparar(fabrica)
    with pytest.raises(DatosInvalidos):
        entregar(fabrica, UsuarioActual(5, "repartidor"), 1, "0000")
    with fabrica() as uow:
        assert uow.ordenes.por_id(1).orden.estado is EstadoOrden.ENVIADA
        assert uow.entregas.por_orden(1).estado == "RECOGIDA"
        assert uow.usuarios.por_id(1).usuario.pedidos_completados == 0

def test_fallo_persistiendo_asignacion_revierte_toda_la_transaccion(fabrica, monkeypatch):
    preparar(fabrica)
    before = None
    with fabrica() as uow:
        before = len(uow.eventos.de_orden(1))
    def falla(*_):
        raise RuntimeError("fallo simulado de persistencia")
    monkeypatch.setattr(EntregaRepoMemoria, "guardar", falla)
    with pytest.raises(RuntimeError):
        entregar(fabrica, UsuarioActual(5, "repartidor"), 1, "4821")
    with fabrica() as uow:
        assert uow.ordenes.por_id(1).orden.estado is EstadoOrden.ENVIADA
        assert uow.entregas.por_orden(1).estado == "RECOGIDA"
        assert uow.usuarios.por_id(1).usuario.pedidos_completados == 0
        assert len(uow.eventos.de_orden(1)) == before
