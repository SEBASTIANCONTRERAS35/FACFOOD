from app.catalogo import servicio

INGENIERIA = (19.3311, -99.1839)


def test_cercanos_con_postgis_coincide_con_memoria(fabrica_pg, fabrica):
    pg = servicio.cercanos(fabrica_pg, *INGENIERIA, 1000, None, None)
    mem = servicio.cercanos(fabrica, *INGENIERIA, 1000, None, None)
    assert {p["nombre"] for p in pg} == {p["nombre"] for p in mem}
    # haversine vs. PostGIS (esferoide): a escala de CU difieren por pocos metros
    dist_mem = {p["nombre"]: p["distancia_m"] for p in mem}
    assert all(abs(p["distancia_m"] - dist_mem[p["nombre"]]) <= 3 for p in pg)
    abiertos = [p["distancia_m"] for p in pg if p["abierto"]]
    assert abiertos == sorted(abiertos)


def test_busqueda_y_categoria_con_postgres(fabrica_pg):
    assert [p["nombre"] for p in servicio.cercanos(fabrica_pg, *INGENIERIA, 2000, "tacos", None)] == ["Tacos Don Memo"]
    assert [p["nombre"] for p in servicio.cercanos(fabrica_pg, *INGENIERIA, 2000, None, "café")] == ["Café Ingeniería"]
