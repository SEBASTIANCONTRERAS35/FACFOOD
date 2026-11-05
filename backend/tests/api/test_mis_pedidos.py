"""Mis pedidos: solo los míos, desde que se pagan, del más reciente al más antiguo."""

from tests.conftest import como

DIANA, SEBASTIAN = 1, 2  # Diana tiene las órdenes de ejemplo #1 y #3; Sebastián, #2 y #4


def test_solo_mis_pedidos_del_mas_reciente_al_mas_antiguo(cliente):
    diana = cliente.get("/usuarios/me/ordenes", headers=como(DIANA)).json()
    assert [o["id"] for o in diana] == [3, 1]  # la #3 se creó después que la #1
    assert diana[0]["punto_venta"]["nombre"] == "Chilaquiles Lupita"
    assert {o["id"] for o in cliente.get("/usuarios/me/ordenes", headers=como(SEBASTIAN)).json()} == {2, 4}


def test_resumen_con_estado_total_y_piezas(cliente):
    orden = next(o for o in cliente.get("/usuarios/me/ordenes", headers=como(DIANA)).json() if o["id"] == 1)
    assert (orden["estado"], orden["metodo_entrega"], orden["piezas"]) == ("PAGADA", "estudiante", 4)
    assert orden["total"] == "82.54" and isinstance(orden["total"], str)
    assert set(orden) == {"id", "estado", "punto_venta", "metodo_entrega", "piezas", "total", "creada_en"}


def test_los_carritos_sin_pagar_no_aparecen(cliente):
    creada = cliente.post("/ordenes", headers=como(DIANA), json={
        "punto_venta_id": 1, "lineas": [{"producto_id": 1, "cantidad": 1}]}).json()
    ids = [o["id"] for o in cliente.get("/usuarios/me/ordenes", headers=como(DIANA)).json()]
    assert creada["id"] not in ids
    cliente.post(f"/ordenes/{creada['id']}/pagar", headers=como(DIANA))
    assert cliente.get("/usuarios/me/ordenes", headers=como(DIANA)).json()[0]["id"] == creada["id"]


def test_muchos_carritos_abandonados_no_ocultan_los_pedidos(cliente):
    for _ in range(55):  # más que el límite de la lista
        cliente.post("/ordenes", headers=como(DIANA), json={"punto_venta_id": 1, "lineas": [{"producto_id": 1, "cantidad": 1}]})
    assert [o["id"] for o in cliente.get("/usuarios/me/ordenes", headers=como(DIANA)).json()] == [3, 1]


def test_sin_sesion_no_hay_pedidos(cliente):
    r = cliente.get("/usuarios/me/ordenes")
    assert r.status_code == 401 and r.json()["codigo"] == "NO_AUTENTICADO"
