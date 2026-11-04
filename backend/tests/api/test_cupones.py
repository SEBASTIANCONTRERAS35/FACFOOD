"""Cupones: nivel de lealtad y cupones filtrados para el usuario de la sesión."""

from tests.conftest import como

DIANA, SEBASTIAN = 1, 2  # Diana: 0 pedidos completados · Sebastián: 3


def codigos(cliente, usuario):
    return {c["codigo"]: c["estado"] for c in cliente.get("/cupones", headers=como(usuario)).json()["cupones"]}


def test_lealtad_y_siguiente_nivel(cliente):
    diana = cliente.get("/cupones", headers=como(DIANA)).json()["lealtad"]
    assert diana == {"nivel": "bronce", "descuento_pct": 0, "pedidos_completados": 0,
                     "siguiente": {"nivel": "plata", "pedidos": 3, "faltan": 3, "descuento_pct": 5}}
    sebastian = cliente.get("/cupones", headers=como(SEBASTIAN)).json()["lealtad"]
    assert (sebastian["nivel"], sebastian["siguiente"]["nivel"], sebastian["siguiente"]["faltan"]) == ("plata", "oro", 7)


def test_cupones_filtrados_para_cada_usuario(cliente):
    assert codigos(cliente, DIANA) == {"BIENVENIDA15": "disponible", "PROMO10": "disponible", "UNICO20": "disponible"}
    assert "BIENVENIDA15" not in codigos(cliente, SEBASTIAN)  # ya tiene pedidos completados
    assert "VENCIDO5" not in codigos(cliente, DIANA)


def test_no_expone_los_contadores_internos(cliente):
    cupon = cliente.get("/cupones", headers=como(DIANA)).json()["cupones"][0]
    assert not {"usos_actuales", "usos_maximos", "id"} & set(cupon)
    assert cupon["pedido_minimo"] == "0.00" and isinstance(cupon["pedido_minimo"], str)


def test_un_cupon_usado_aparece_como_usado_y_al_final(cliente):
    orden = cliente.post("/ordenes", headers=como(DIANA), json={
        "punto_venta_id": 1, "lineas": [{"producto_id": 1, "cantidad": 2}]}).json()
    cliente.post(f"/ordenes/{orden['id']}/cupon", headers=como(DIANA), json={"codigo": "BIENVENIDA15"})
    cliente.post(f"/ordenes/{orden['id']}/pagar", headers=como(DIANA))
    lista = cliente.get("/cupones", headers=como(DIANA)).json()["cupones"]
    assert lista[-1]["codigo"] == "BIENVENIDA15" and lista[-1]["estado"] == "usado"


def test_un_cupon_agotado_desaparece_salvo_para_quien_lo_uso(cliente):
    orden = cliente.post("/ordenes", headers=como(SEBASTIAN), json={
        "punto_venta_id": 1, "lineas": [{"producto_id": 1, "cantidad": 10}]}).json()
    cliente.post(f"/ordenes/{orden['id']}/cupon", headers=como(SEBASTIAN), json={"codigo": "UNICO20"})
    cliente.post(f"/ordenes/{orden['id']}/pagar", headers=como(SEBASTIAN))
    assert codigos(cliente, SEBASTIAN)["UNICO20"] == "usado"
    assert "UNICO20" not in codigos(cliente, DIANA)


def test_sin_sesion_no_hay_cupones(cliente):
    assert cliente.get("/cupones").status_code == 401
