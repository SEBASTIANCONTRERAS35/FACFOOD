INGENIERIA = {"lat": 19.3311, "lon": -99.1839}


def test_cercanos_ordenados_y_con_distancia(cliente):
    puestos = cliente.get("/puntos-venta", params={**INGENIERIA, "radio": 500}).json()
    abiertos = [p for p in puestos if p["abierto"]]
    assert [p["distancia_m"] for p in abiertos] == sorted(p["distancia_m"] for p in abiertos)
    assert all(p["distancia_m"] <= 500 for p in puestos)
    assert {"Tacos Don Memo", "Café Ingeniería"} <= {p["nombre"] for p in puestos}


def test_los_cerrados_van_al_final(cliente):
    puestos = cliente.get("/puntos-venta", params={**INGENIERIA, "radio": 2000}).json()
    estados = [p["abierto"] for p in puestos]
    assert estados == sorted(estados, reverse=True)
    assert puestos[-1]["nombre"] == "Quesadillas Las Islas"


def test_un_radio_pequeno_deja_fuera_lo_lejano(cliente):
    cerca = cliente.get("/puntos-venta", params={**INGENIERIA, "radio": 150}).json()
    assert {p["nombre"] for p in cerca} == {"Tacos Don Memo", "Café Ingeniería"}


def test_filtro_por_categoria_y_busqueda(cliente):
    tacos = cliente.get("/puntos-venta", params={**INGENIERIA, "categoria": "tacos"}).json()
    assert [p["nombre"] for p in tacos] == ["Tacos Don Memo"]
    cafe = cliente.get("/puntos-venta", params={**INGENIERIA, "q": "café"}).json()
    assert [p["nombre"] for p in cafe] == ["Café Ingeniería"]


def test_sin_ubicacion_usa_la_facultad_de_ingenieria(cliente):
    assert cliente.get("/puntos-venta").json() == cliente.get("/puntos-venta", params=INGENIERIA).json()


def test_coordenadas_o_radio_invalidos_dan_422(cliente):
    assert cliente.get("/puntos-venta", params={"lat": 200}).status_code == 422
    assert cliente.get("/puntos-venta", params={"radio": 999999}).status_code == 422


def test_categorias(cliente):
    cats = cliente.get("/puntos-venta/categorias").json()
    assert "Tacos" in cats and cats == sorted(cats)


def test_detalle_del_puesto(cliente):
    p = cliente.get("/puntos-venta/1", params=INGENIERIA).json()
    assert p["nombre"] == "Tacos Don Memo" and p["distancia_m"] > 0 and p["horario_cierre"] == "17:00"
    assert cliente.get("/puntos-venta/1").json()["distancia_m"] is None
    assert cliente.get("/puntos-venta/999").status_code == 404
