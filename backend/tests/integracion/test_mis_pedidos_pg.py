from app.checkout import servicio
from app.shared.auth import UsuarioActual


def test_mis_pedidos_con_postgres(fabrica_pg):
    diana = servicio.mis_ordenes(fabrica_pg, UsuarioActual(1, "comprador"))
    assert [o["id"] for o in diana] == [3, 1]
    assert diana[1]["piezas"] == 4 and diana[1]["total"] == "82.54"
    assert {o["id"] for o in servicio.mis_ordenes(fabrica_pg, UsuarioActual(2, "comprador"))} == {2, 4}


def test_carritos_abandonados_no_desplazan_los_pedidos_en_postgres(fabrica_pg):
    diana = UsuarioActual(1, "comprador")
    for _ in range(55):
        servicio.crear_orden(fabrica_pg, diana, 1, [(1, 1)], "pickup", None)
    assert [o["id"] for o in servicio.mis_ordenes(fabrica_pg, diana)] == [3, 1]
