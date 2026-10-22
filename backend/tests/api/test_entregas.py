from tests.conftest import como

def test_disponibles_solo_entrega_estudiantil_elegible(cliente):
    r = cliente.get("/entregas/disponibles", headers=como(5))
    assert r.status_code == 200
    datos = r.json()["entregas"]
    assert [e["orden_id"] for e in datos] == [1, 3]
    assert all(e["estado"] in {"PAGADA", "EN_PREPARACION"} for e in datos)
    assert all(e["destino"] for e in datos)
    assert all("ganancia" in e and "distancia_km" in e for e in datos)

def test_disponibles_exige_repartidor(cliente):
    assert cliente.get("/entregas/disponibles").status_code == 401
    assert cliente.get("/entregas/disponibles", headers=como(1)).status_code == 403

def test_aceptar_asigna_y_retira_de_disponibles(cliente, fabrica):
    r = cliente.post("/entregas/1/aceptar", headers=como(5))
    assert r.status_code == 201
    assert r.json() == {"orden_id": 1, "estado": "ACEPTADA"}
    assert [e["orden_id"] for e in cliente.get("/entregas/disponibles", headers=como(5)).json()["entregas"]] == [3]
    with fabrica() as uow:
        asignacion = uow.entregas.por_orden(1)
        assert asignacion.repartidor_id == 5
        assert asignacion.estado == "ACEPTADA"
        assert asignacion.aceptada_en is not None
        # La aceptación no altera el estado de la orden.
        assert uow.ordenes.por_id(1).orden.estado.value == "PAGADA"

def test_doble_aceptacion_responde_409(cliente):
    assert cliente.post("/entregas/1/aceptar", headers=como(5)).status_code == 201
    respuesta = cliente.post("/entregas/1/aceptar", headers=como(5))
    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "ENTREGA_YA_ACEPTADA"

def test_no_repartidor_no_puede_aceptar(cliente):
    assert cliente.post("/entregas/1/aceptar", headers=como(1)).status_code == 403

def test_orden_no_elegible_y_orden_inexistente(cliente):
    assert cliente.post("/entregas/2/aceptar", headers=como(5)).status_code == 409
    assert cliente.post("/entregas/999/aceptar", headers=como(5)).status_code == 404
