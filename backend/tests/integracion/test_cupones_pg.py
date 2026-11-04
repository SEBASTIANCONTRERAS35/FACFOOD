from app.checkout import servicio
from app.shared.auth import UsuarioActual


def test_cupones_con_postgres(fabrica_pg):
    diana = servicio.cupones_del_usuario(fabrica_pg, UsuarioActual(1, "comprador"))
    assert {c["codigo"] for c in diana["cupones"]} == {"BIENVENIDA15", "PROMO10", "UNICO20"}
    assert diana["lealtad"]["siguiente"]["faltan"] == 3
    sebastian = servicio.cupones_del_usuario(fabrica_pg, UsuarioActual(2, "comprador"))
    assert "BIENVENIDA15" not in {c["codigo"] for c in sebastian["cupones"]}
