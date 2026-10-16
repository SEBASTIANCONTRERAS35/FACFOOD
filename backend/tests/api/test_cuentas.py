from tests.conftest import como

NUEVO = {
    "nombre": "  Ana   López ",
    "credencial_unam": "320123456",
    "correo": "Ana.Lopez@Comunidad.UNAM.mx",
    "password": "segura123",
    "consentimiento_datos": True,
}


def test_registro_crea_comprador_y_devuelve_sesion(cliente):
    r = cliente.post("/auth/registro", json=NUEVO)
    assert r.status_code == 201
    datos = r.json()
    assert datos["usuario"]["nombre"] == "Ana López"
    assert datos["usuario"]["correo"] == "ana.lopez@comunidad.unam.mx"
    assert datos["usuario"]["rol"] == "comprador"
    assert datos["usuario"]["nivel_lealtad"] == "bronce"
    yo = cliente.get("/usuarios/me", headers={"Authorization": f"Bearer {datos['access_token']}"})
    assert yo.status_code == 200 and yo.json()["id"] == datos["usuario"]["id"]


def test_registro_sin_consentimiento_se_rechaza(cliente):
    r = cliente.post("/auth/registro", json={**NUEVO, "consentimiento_datos": False})
    assert r.status_code == 422
    assert r.json()["codigo"] == "CONSENTIMIENTO_REQUERIDO"


def test_la_contrasena_no_se_guarda_en_texto_plano(cliente, fabrica):
    cliente.post("/auth/registro", json=NUEVO)
    with fabrica() as uow:
        cuenta = uow.usuarios.por_correo(NUEVO["correo"])
    assert b"segura123" not in cuenta.usuario.password_hash


def test_correo_o_credencial_repetidos_dan_409(cliente):
    assert cliente.post("/auth/registro", json=NUEVO).status_code == 201
    mismo_correo = cliente.post("/auth/registro", json={**NUEVO, "credencial_unam": "320000000"})
    assert mismo_correo.status_code == 409 and mismo_correo.json()["codigo"] == "CORREO_REGISTRADO"
    misma_credencial = cliente.post("/auth/registro", json={**NUEVO, "correo": "otra@unam.mx"})
    assert misma_credencial.status_code == 409 and misma_credencial.json()["codigo"] == "CREDENCIAL_REGISTRADA"


def test_validaciones_de_formato_en_espanol(cliente):
    r = cliente.post("/auth/registro", json={**NUEVO, "credencial_unam": "123", "password": "corta", "correo": "x"})
    assert r.status_code == 422
    mensajes = " ".join(e["msg"] for e in r.json()["detail"])
    assert "9 dígitos" in mensajes and "8 caracteres" in mensajes and "correo válido" in mensajes


def test_login_correcto_e_incorrecto(cliente):
    ok = cliente.post("/auth/login", json={"correo": "DIANA@facfood.mx", "password": "facfood123"})
    assert ok.status_code == 200 and ok.json()["usuario"]["id"] == 1
    mal = cliente.post("/auth/login", json={"correo": "diana@facfood.mx", "password": "otra-cosa"})
    nadie = cliente.post("/auth/login", json={"correo": "nadie@facfood.mx", "password": "facfood123"})
    assert mal.status_code == nadie.status_code == 401
    assert mal.json() == nadie.json()  # no revela si el correo existe


def test_token_invalido_da_401(cliente):
    r = cliente.get("/usuarios/me", headers={"Authorization": "Bearer no-es-un-token"})
    assert r.status_code == 401


def test_perfil_dual_requiere_3_pedidos(cliente):
    diana = cliente.post("/usuarios/me/vendedor", headers=como(1))  # 0 pedidos
    assert diana.status_code == 422 and diana.json()["codigo"] == "PERFIL_NO_ELEGIBLE"
    sebastian = cliente.post("/usuarios/me/vendedor", headers=como(2))  # 3 pedidos
    assert sebastian.status_code == 200 and sebastian.json()["rol"] == "vendedor"
    assert cliente.get("/usuarios/me", headers=como(2)).json()["puede_vender"] is False


def test_repartidor_no_puede_volverse_vendedor(cliente):
    r = cliente.post("/usuarios/me/vendedor", headers=como(5))
    assert r.status_code == 409


def test_nivel_de_lealtad_en_el_perfil(cliente):
    assert cliente.get("/usuarios/me", headers=como(2)).json()["nivel_lealtad"] == "plata"
