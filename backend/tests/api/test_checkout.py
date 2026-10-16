"""Checkout (vista 04): crear orden, cupón, lealtad, entrega y pago."""

import threading

from tests.conftest import como

DIANA, SEBASTIAN, MEMO = 1, 2, 3  # Diana: 0 pedidos (bronce) · Sebastián: 3 pedidos (plata)
DON_MEMO, CAFE, QUESADILLAS = 1, 2, 8  # Café solo pickup · Quesadillas cerrado
PASTOR, SUADERO, QUESADILLA, AGUA = 1, 2, 3, 5


def crear(cliente, usuario=DIANA, lineas=((PASTOR, 2), (QUESADILLA, 1)), metodo="pickup", destino=None, punto=DON_MEMO):
    return cliente.post(
        "/ordenes",
        headers=como(usuario),
        json={"punto_venta_id": punto, "lineas": [{"producto_id": p, "cantidad": c} for p, c in lineas],
              "metodo_entrega": metodo, "destino_id": destino},
    )


def destino(cliente, nombre):
    return next(d["id"] for d in cliente.get("/destinos").json() if d["nombre"] == nombre)


# ---- El caso de la pantalla 04 ----
def test_caso_de_la_pantalla_04_de_punta_a_punta(cliente, fabrica):
    orden = crear(cliente).json()
    assert (orden["estado"], orden["subtotal"], orden["descuento"]) == ("CREADA", "66.00", "0.00")
    assert [(l["nombre"], l["cantidad"], l["importe"]) for l in orden["lineas"]] == [
        ("Taco de pastor", 2, "36.00"), ("Quesadilla de queso", 1, "30.00"),
    ]

    con_cupon = cliente.post(f"/ordenes/{orden['id']}/cupon", headers=como(DIANA), json={"codigo": "bienvenida15"}).json()
    assert (con_cupon["descuento"], con_cupon["origen_descuento"], con_cupon["cupon"]) == ("9.90", "cupon", "BIENVENIDA15")
    assert (con_cupon["iva"], con_cupon["envio"], con_cupon["total"]) == ("8.98", "0.00", "65.08")

    pagada = cliente.post(f"/ordenes/{orden['id']}/pagar", headers=como(DIANA)).json()
    assert pagada["estado"] == "PAGADA" and pagada["total"] == "65.08"
    assert pagada["factura_folio"] is not None and pagada["codigo_entrega"] is None  # pickup: sin código

    with fabrica() as uow:
        assert [e.estado for e in uow.eventos.de_orden(orden["id"])] == ["CREADA", "PAGADA"]
        assert uow.cupones.por_codigo("BIENVENIDA15").cupon.usos_actuales == 1
        assert b'Total="65.08"' in uow.facturas.de_orden(orden["id"]).factura.xml_data


def test_el_precio_lo_dicta_el_servidor(cliente):
    r = cliente.post("/ordenes", headers=como(DIANA), json={
        "punto_venta_id": DON_MEMO, "lineas": [{"producto_id": PASTOR, "cantidad": 1, "precio": "0.01"}],
    })
    assert r.json()["lineas"][0]["precio_unitario"] == "18.00"


def test_lineas_repetidas_se_juntan(cliente):
    orden = crear(cliente, lineas=((PASTOR, 1), (PASTOR, 2))).json()
    assert [(l["producto_id"], l["cantidad"]) for l in orden["lineas"]] == [(PASTOR, 3)]


# ---- Lealtad (CRM) ----
def test_cliente_plata_recibe_su_descuento_sin_cupon(cliente):
    orden = crear(cliente, usuario=SEBASTIAN).json()  # 66 * 5% = 3.30
    assert (orden["descuento"], orden["origen_descuento"]) == ("3.30", "lealtad")


def test_bienvenida_es_solo_para_el_primer_pedido(cliente):
    orden = crear(cliente, usuario=SEBASTIAN).json()
    r = cliente.post(f"/ordenes/{orden['id']}/cupon", headers=como(SEBASTIAN), json={"codigo": "BIENVENIDA15"})
    assert r.status_code == 422 and "primer pedido" in r.json()["detail"]


def test_un_cupon_de_uno_por_usuario_no_se_repite(cliente):
    primera = crear(cliente).json()
    cliente.post(f"/ordenes/{primera['id']}/cupon", headers=como(DIANA), json={"codigo": "BIENVENIDA15"})
    cliente.post(f"/ordenes/{primera['id']}/pagar", headers=como(DIANA))
    segunda = crear(cliente).json()
    r = cliente.post(f"/ordenes/{segunda['id']}/cupon", headers=como(DIANA), json={"codigo": "BIENVENIDA15"})
    assert r.status_code == 422 and r.json()["detail"] == "Ya usaste este cupón"


# ---- Cupones inválidos ----
def test_cupones_invalidos(cliente):
    orden = crear(cliente).json()
    url = f"/ordenes/{orden['id']}/cupon"
    assert cliente.post(url, headers=como(DIANA), json={"codigo": "NOEXISTE"}).status_code == 404
    vencido = cliente.post(url, headers=como(DIANA), json={"codigo": "VENCIDO5"})
    assert vencido.status_code == 422 and vencido.json()["codigo"] == "CUPON_INVALIDO"
    minimo = cliente.post(url, headers=como(DIANA), json={"codigo": "PROMO10"})  # mínimo $100, subtotal $66
    assert minimo.status_code == 422 and "mínimo" in minimo.json()["detail"]
    # El cupón rechazado no queda pegado a la orden: se puede pagar sin descuento
    assert cliente.post(f"/ordenes/{orden['id']}/pagar", headers=como(DIANA)).json()["descuento"] == "0.00"


def test_cupon_agotado_antes_de_pagar_se_puede_quitar(cliente):
    a, b = crear(cliente).json(), crear(cliente, usuario=SEBASTIAN, lineas=((PASTOR, 10),)).json()
    for orden, usuario in ((a, DIANA), (b, SEBASTIAN)):
        assert cliente.post(f"/ordenes/{orden['id']}/cupon", headers=como(usuario), json={"codigo": "UNICO20"}).status_code == 200
    assert cliente.post(f"/ordenes/{a['id']}/pagar", headers=como(DIANA)).status_code == 200
    agotado = cliente.post(f"/ordenes/{b['id']}/pagar", headers=como(SEBASTIAN))
    assert agotado.status_code == 422 and "límite de usos" in agotado.json()["detail"]
    sin = cliente.delete(f"/ordenes/{b['id']}/cupon", headers=como(SEBASTIAN)).json()
    assert sin["origen_descuento"] == "lealtad"  # vuelve a su 5% de plata
    assert cliente.post(f"/ordenes/{b['id']}/pagar", headers=como(SEBASTIAN)).json()["estado"] == "PAGADA"


def test_dos_pagos_simultaneos_con_un_cupon_de_un_solo_uso(cliente):
    ordenes = [crear(cliente).json(), crear(cliente, usuario=SEBASTIAN, lineas=((PASTOR, 10),)).json()]
    duenos = [DIANA, SEBASTIAN]
    for o, u in zip(ordenes, duenos):
        cliente.post(f"/ordenes/{o['id']}/cupon", headers=como(u), json={"codigo": "UNICO20"})
    resultados, salida = [], threading.Barrier(2)

    def pagar(o, u):
        salida.wait()
        resultados.append(cliente.post(f"/ordenes/{o['id']}/pagar", headers=como(u)).status_code)

    hilos = [threading.Thread(target=pagar, args=par) for par in zip(ordenes, duenos)]
    [h.start() for h in hilos]
    [h.join() for h in hilos]
    assert sorted(resultados) == [200, 422]


# ---- Entrega por estudiante (Strategy) ----
def test_entrega_estudiante_cobra_5_pesos_por_km_y_genera_codigo(cliente):
    arquitectura = destino(cliente, "Facultad de Arquitectura")
    orden = crear(cliente, metodo="estudiante", destino=arquitectura).json()
    km = float(orden["distancia_km"])
    assert 0.3 < km < 1.0 and orden["destino"]["nombre"] == "Facultad de Arquitectura"
    assert orden["envio"] == f"{round(km * 5, 2):.2f}"
    pagada = cliente.post(f"/ordenes/{orden['id']}/pagar", headers=como(DIANA)).json()
    assert len(pagada["codigo_entrega"]) == 4 and pagada["codigo_entrega"].isdigit()


def test_cambiar_de_entrega_a_pickup_quita_el_envio(cliente):
    orden = crear(cliente, metodo="estudiante", destino=destino(cliente, "Biblioteca Central")).json()
    pickup = cliente.patch(f"/ordenes/{orden['id']}/entrega", headers=como(DIANA), json={"metodo_entrega": "pickup"}).json()
    assert (pickup["envio"], pickup["destino"], pickup["metodo_entrega"]) == ("0.00", None, "pickup")


def test_entrega_requiere_destino_y_un_puesto_que_la_ofrezca(cliente):
    sin_destino = crear(cliente, metodo="estudiante")
    assert sin_destino.status_code == 422 and sin_destino.json()["codigo"] == "DESTINO_REQUERIDO"
    cafe = crear(cliente, punto=CAFE, lineas=((6, 1),), metodo="estudiante", destino=1)
    assert cafe.status_code == 422 and cafe.json()["codigo"] == "SIN_ENTREGA"


# ---- Reglas y permisos ----
def test_producto_de_otro_puesto_o_puesto_cerrado(cliente):
    otro = crear(cliente, lineas=((6, 1),))  # el producto 6 es del Café
    assert otro.status_code == 422 and otro.json()["codigo"] == "PRODUCTO_NO_ENCONTRADO"
    cerrado = crear(cliente, punto=QUESADILLAS, lineas=((25, 1),))
    assert cerrado.status_code == 409 and cerrado.json()["codigo"] == "PUESTO_CERRADO"


def test_cantidades_invalidas(cliente):
    assert crear(cliente, lineas=((PASTOR, 0),)).status_code == 422
    assert crear(cliente, lineas=()).status_code == 422


def test_no_se_paga_dos_veces_ni_se_cambia_una_orden_pagada(cliente):
    orden = crear(cliente).json()
    assert cliente.post(f"/ordenes/{orden['id']}/pagar", headers=como(DIANA)).status_code == 200
    otra_vez = cliente.post(f"/ordenes/{orden['id']}/pagar", headers=como(DIANA))
    assert otra_vez.status_code == 409 and otra_vez.json()["codigo"] == "ORDEN_YA_PAGADA"
    cambio = cliente.patch(f"/ordenes/{orden['id']}/entrega", headers=como(DIANA), json={"metodo_entrega": "pickup"})
    assert cambio.status_code == 409


def test_rfc_invalido_no_cobra(cliente, fabrica):
    orden = crear(cliente).json()
    r = cliente.post(f"/ordenes/{orden['id']}/pagar", headers=como(DIANA), json={"rfc": "RFC-MALO"})
    assert r.status_code == 422
    with fabrica() as uow:
        assert uow.ordenes.por_id(orden["id"]).orden.estado.value == "CREADA"  # se revirtió todo


def test_rfc_propio_en_la_factura(cliente, fabrica):
    orden = crear(cliente).json()
    cliente.post(f"/ordenes/{orden['id']}/pagar", headers=como(DIANA), json={"rfc": "romd010101ab1"})
    with fabrica() as uow:
        assert uow.facturas.de_orden(orden["id"]).factura.rfc_receptor == "ROMD010101AB1"


def test_la_orden_de_otro_usuario_no_existe_para_mi(cliente):
    orden = crear(cliente).json()
    assert cliente.post(f"/ordenes/{orden['id']}/pagar", headers=como(MEMO)).status_code == 404


def test_sin_sesion_no_se_puede_pedir(cliente):
    assert cliente.post("/ordenes", json={"punto_venta_id": 1, "lineas": [{"producto_id": 1, "cantidad": 1}]}).status_code == 401


def test_destinos(cliente):
    nombres = [d["nombre"] for d in cliente.get("/destinos").json()]
    assert "Facultad de Ingeniería" in nombres and nombres == sorted(nombres)
