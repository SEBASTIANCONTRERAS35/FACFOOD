from tests.conftest import como


def test_comprador_consulta_su_orden_con_eventos_y_codigo(cliente):
    respuesta = cliente.get("/ordenes/1", headers=como(1))

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["id"] == 1
    assert datos["punto_venta"]["nombre"] == "Tacos Don Memo"
    assert datos["metodo_entrega"] == "estudiante"
    assert len(datos["total"].split(".")[-1]) == 2
    assert [evento["estado"] for evento in datos["eventos"]] == ["CREADA", "PAGADA"]
    assert datos["codigo_entrega"] == "4821"


def test_codigo_no_se_devuelve_para_pickup(cliente):
    respuesta = cliente.get("/ordenes/2", headers=como(2))

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["metodo_entrega"] == "pickup"
    assert datos["codigo_entrega"] is None


def test_codigo_no_se_devuelve_antes_del_pago(cliente):
    creada = cliente.post("/ordenes", headers=como(1), json={
        "punto_venta_id": 1,
        "lineas": [{"producto_id": 1, "cantidad": 1}],
        "metodo_entrega": "estudiante",
        "destino_id": 2,
    })
    assert creada.status_code == 201

    seguimiento = cliente.get(f"/ordenes/{creada.json()['id']}", headers=como(1))
    assert seguimiento.status_code == 200
    assert seguimiento.json()["codigo_entrega"] is None


def test_codigo_malformado_no_se_devuelve(cliente, fabrica):
    with fabrica() as uow:
        orden = uow.ordenes.por_id(1)
        orden.codigo_entrega = "12AB"
        uow.ordenes.guardar(orden)
        uow.commit()

    respuesta = cliente.get("/ordenes/1", headers=como(1))
    assert respuesta.status_code == 200
    assert respuesta.json()["codigo_entrega"] is None


def test_orden_ajena_se_presenta_como_inexistente(cliente):
    respuesta = cliente.get("/ordenes/1", headers=como(2))

    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == "Esa orden no existe"


def test_rol_no_comprador_no_consulta_seguimiento(cliente):
    # La orden 1 es de Diana: para otro usuario no existe (no se revela que existe).
    respuesta = cliente.get("/ordenes/1", headers=como(3))
    assert respuesta.status_code == 404


def test_comprador_que_se_vuelve_vendedor_sigue_viendo_sus_pedidos(cliente):
    orden = cliente.post("/ordenes", headers=como(2), json={"punto_venta_id": 1, "lineas": [{"producto_id": 1, "cantidad": 1}]}).json()
    cliente.post(f"/ordenes/{orden['id']}/pagar", headers=como(2))
    assert cliente.post("/usuarios/me/vendedor", headers=como(2)).json()["rol"] == "vendedor"
    assert cliente.get(f"/ordenes/{orden['id']}", headers=como(2)).status_code == 200
    assert cliente.get(f"/ordenes/{orden['id']}/factura", headers=como(2)).status_code == 200


def test_seguimiento_requiere_sesion(cliente):
    assert cliente.get("/ordenes/1").status_code == 401


def test_comprador_descarga_factura_xml_propia(cliente):
    respuesta = cliente.get("/ordenes/1/factura", headers=como(1))

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("application/xml")
    assert "attachment;" in respuesta.headers["content-disposition"]
    assert b"<Comprobante" in respuesta.content
    assert b'Folio="' in respuesta.content


def test_factura_de_orden_ajena_es_inexistente(cliente):
    respuesta = cliente.get("/ordenes/1/factura", headers=como(2))
    assert respuesta.status_code == 404


def test_factura_no_esta_disponible_antes_del_pago(cliente):
    creada = cliente.post("/ordenes", headers=como(1), json={
        "punto_venta_id": 1,
        "lineas": [{"producto_id": 1, "cantidad": 1}],
        "metodo_entrega": "pickup",
    })
    assert creada.status_code == 201

    factura = cliente.get(f"/ordenes/{creada.json()['id']}/factura", headers=como(1))
    assert factura.status_code == 404
