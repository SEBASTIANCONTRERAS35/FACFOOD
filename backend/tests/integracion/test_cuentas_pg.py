from app.cuentas import servicio


def test_registro_y_login_con_postgres(fabrica_pg):
    cuenta = servicio.registrar(fabrica_pg, "Ana López", "320123456", "ana@unam.mx", "segura123", True)
    assert cuenta.id is not None
    assert servicio.autenticar(fabrica_pg, "ana@unam.mx", "segura123").id == cuenta.id


def test_perfil_dual_se_guarda_en_postgres(fabrica_pg):
    servicio.convertirse_en_vendedor(fabrica_pg, 2)
    assert servicio.obtener(fabrica_pg, 2).usuario.rol == "vendedor"
