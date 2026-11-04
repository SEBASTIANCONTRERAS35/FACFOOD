from app.checkout import servicio
from app.shared.auth import UsuarioActual


def test_mis_pedidos_con_postgres(fabrica_pg):
    diana = servicio.mis_ordenes(fabrica_pg, UsuarioActual(1, "comprador"))
    assert [o["id"] for o in diana] == [3, 1]
    assert diana[1]["piezas"] == 4 and diana[1]["total"] == "82.54"
    assert {o["id"] for o in servicio.mis_ordenes(fabrica_pg, UsuarioActual(2, "comprador"))} == {2, 4}
