from datetime import datetime, timezone

from app.domain.erp.orden import EstadoOrden
from app.ports.repositorios import CuentaUsuario, EntregaRegistro, EventoOrden
from app.domain.usuario import Usuario
from tests.conftest import como

def asignar(fabrica, *, orden_id=1, repartidor_id=5, estado_entrega="ACEPTADA", estado_orden=None, codigo=None):
    with fabrica() as uow:
        orden = uow.ordenes.por_id(orden_id)
        if estado_orden is not None:
            if estado_orden in {"EN_PREPARACION", "ENVIADA", "ENTREGADA"} and orden.orden.estado is EstadoOrden.PAGADA:
                orden.orden.avanzar_estado(EstadoOrden.EN_PREPARACION)
                uow.eventos.agregar(EventoOrden(orden_id, "EN_PREPARACION", datetime.now(timezone.utc), 3))
            if estado_orden in {"ENVIADA", "ENTREGADA"}:
                orden.orden.avanzar_estado(EstadoOrden.ENVIADA)
                uow.eventos.agregar(EventoOrden(orden_id, "ENVIADA", datetime.now(timezone.utc), 5))
            if estado_orden == "ENTREGADA":
                orden.orden.avanzar_estado(EstadoOrden.ENTREGADA)
                uow.eventos.agregar(EventoOrden(orden_id, "ENTREGADA", datetime.now(timezone.utc), 5))
            uow.ordenes.guardar(orden)
        if codigo is not None:
            orden.codigo_entrega = codigo
            uow.ordenes.guardar(orden)
        uow.entregas.agregar(EntregaRegistro(
            None, orden_id, repartidor_id, estado_entrega,
            datetime.now(timezone.utc),
            datetime.now(timezone.utc) if estado_entrega in {"RECOGIDA", "ENTREGADA"} else None,
            datetime.now(timezone.utc) if estado_entrega == "ENTREGADA" else None,
        ))
        uow.commit()

def nuevo_repartidor(fabrica):
    with fabrica() as uow:
        cuenta = uow.usuarios.agregar(CuentaUsuario(
            None, "otro.repartidor@facfood.mx",
            Usuario.restaurar("Otro repartidor", "319000006", None, "repartidor", 0),
        ))
        uow.commit()
        return cuenta.id

def preparar_recogida(fabrica):
    asignar(fabrica, estado_orden="EN_PREPARACION")

def preparar_entrega(fabrica, codigo="4821"):
    asignar(fabrica, estado_entrega="RECOGIDA", estado_orden="ENVIADA", codigo=codigo)

def test_detalle_solo_para_repartidor_asignado(cliente, fabrica):
    asignar(fabrica)
    r = cliente.get("/entregas/1", headers=como(5))
    assert r.status_code == 200
    datos = r.json()
    assert datos["estado_orden"] == "PAGADA"
    assert datos["estado_entrega"] == "ACEPTADA"
    assert datos["puesto"]["nombre"] == "Tacos Don Memo"
    assert "codigo_entrega" not in datos

def test_detalle_no_asignado_ajeno_o_inexistente_es_404(cliente, fabrica):
    asignar(fabrica)
    otro = nuevo_repartidor(fabrica)
    assert cliente.get("/entregas/3", headers=como(5)).status_code == 404
    asignar(fabrica, orden_id=3, repartidor_id=otro)
    assert cliente.get("/entregas/3", headers=como(5)).status_code == 404
    assert cliente.get("/entregas/999", headers=como(5)).status_code == 404

def test_detalle_y_acciones_requieren_rol_repartidor(cliente):
    assert cliente.get("/entregas/1").status_code == 401
    assert cliente.get("/entregas/1", headers=como(1)).status_code == 403
    assert cliente.post("/entregas/1/recoger", headers=como(1)).status_code == 403
    assert cliente.post("/entregas/1/entregar", headers=como(1), json={"codigo_entrega":"4821"}).status_code == 403

def test_recogida_rechaza_pedido_pagado_sin_mutaciones(cliente, fabrica):
    asignar(fabrica)
    r = cliente.post("/entregas/1/recoger", headers=como(5))
    assert r.status_code == 409
    with fabrica() as uow:
        assert uow.ordenes.por_id(1).orden.estado.value == "PAGADA"
        assert uow.entregas.por_orden(1).estado == "ACEPTADA"
        assert len(uow.eventos.de_orden(1)) == 2

def test_recogida_avanza_orden_asignacion_y_evento(cliente, fabrica):
    preparar_recogida(fabrica)
    r = cliente.post("/entregas/1/recoger", headers=como(5))
    assert r.status_code == 200
    assert r.json()["estado_orden"] == "ENVIADA"
    assert r.json()["estado_entrega"] == "RECOGIDA"
    with fabrica() as uow:
        evento = uow.eventos.de_orden(1)[-1]
        assert evento.estado == "ENVIADA" and evento.actor_id == 5 and evento.creado_en
        assert uow.entregas.por_orden(1).recogida_en

def test_recogida_no_se_puede_repetir(cliente, fabrica):
    preparar_recogida(fabrica)
    assert cliente.post("/entregas/1/recoger", headers=como(5)).status_code == 200
    assert cliente.post("/entregas/1/recoger", headers=como(5)).status_code == 409

def test_codigo_incorrecto_no_modifica_datos(cliente, fabrica):
    preparar_entrega(fabrica)
    r = cliente.post("/entregas/1/entregar", headers=como(5), json={"codigo_entrega":"0000"})
    assert r.status_code == 422
    assert "0000" not in r.text
    with fabrica() as uow:
        assert uow.ordenes.por_id(1).orden.estado.value == "ENVIADA"
        assert uow.entregas.por_orden(1).estado == "RECOGIDA"
        assert uow.usuarios.por_id(1).usuario.pedidos_completados == 0
        assert [e.estado for e in uow.eventos.de_orden(1)][-1] == "ENVIADA"

def test_codigo_con_ceros_iniciales_completa_una_sola_vez(cliente, fabrica):
    preparar_entrega(fabrica, codigo="0042")
    payload = {"codigo_entrega":"0042"}
    r = cliente.post("/entregas/1/entregar", headers=como(5), json=payload)
    assert r.status_code == 200
    assert r.json()["estado_orden"] == "ENTREGADA"
    assert r.json()["estado_entrega"] == "ENTREGADA"
    reintento = cliente.post("/entregas/1/entregar", headers=como(5), json=payload)
    assert reintento.status_code == 200
    with fabrica() as uow:
        assert uow.usuarios.por_id(1).usuario.pedidos_completados == 1
        assert uow.entregas.por_orden(1).entregada_en
        eventos = uow.eventos.de_orden(1)
        assert eventos[-1].estado == "ENTREGADA" and eventos[-1].actor_id == 5

def test_codigo_debe_ser_cadena_de_cuatro_digitos_ascii(cliente, fabrica):
    preparar_entrega(fabrica)
    for codigo in ("123", "12A4", "12345", "".join(chr(n) for n in (0xFF11, 0xFF12, 0xFF13, 0xFF14))):
        r = cliente.post("/entregas/1/entregar", headers=como(5), json={"codigo_entrega":codigo})
        assert r.status_code == 422
        assert codigo not in r.text
    r = cliente.post("/entregas/1/entregar", headers=como(5), json={"codigo_entrega":1234})
    assert r.status_code == 422
    assert "1234" not in r.text
