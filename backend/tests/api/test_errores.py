"""Errores en formato RFC 7807 (Problem Details) y su documentación en Swagger."""

from tests.conftest import como

CAMPOS_RFC = {"type", "title", "status", "detail", "instance", "codigo"}


def test_validacion_de_dto_responde_400_problem_details(cliente):
    r = cliente.post("/auth/registro", json={
        "nombre": "A", "credencial_unam": "12", "correo": "x", "password": "corta", "consentimiento_datos": True,
    })
    assert r.status_code == 400
    assert r.headers["content-type"].startswith("application/problem+json")
    cuerpo = r.json()
    assert CAMPOS_RFC | {"invalid_params"} == set(cuerpo)
    assert (cuerpo["status"], cuerpo["codigo"], cuerpo["instance"]) == (400, "VALIDACION", "/auth/registro")
    assert cuerpo["type"].endswith("#validacion")
    assert {p["name"] for p in cuerpo["invalid_params"]} == {"nombre", "credencial_unam", "correo", "password"}


def test_ningun_error_repite_lo_que_envio_el_usuario(cliente):
    r = cliente.post("/auth/registro", json={
        "nombre": "Ana López", "credencial_unam": "320123456", "correo": "ana@unam.mx",
        "password": "mi-secreta-" + "x" * 80, "consentimiento_datos": True,
    })
    assert r.status_code == 400
    assert "mi-secreta" not in r.text  # FastAPI por defecto devolvía el valor en `input`


def test_campo_faltante_se_nombra_en_invalid_params(cliente):
    r = cliente.post("/ordenes", headers=como(1), json={"lineas": [{"producto_id": 1, "cantidad": 1}]})
    assert r.status_code == 400
    assert {"name": "punto_venta_id", "reason": "Field required"} in r.json()["invalid_params"]


def test_errores_de_negocio_y_de_estado_tambien_son_rfc_7807(cliente):
    sin_sesion = cliente.get("/usuarios/me")
    assert sin_sesion.status_code == 401 and CAMPOS_RFC == set(sin_sesion.json())
    cupon = cliente.post("/ordenes", headers=como(1), json={"punto_venta_id": 1, "lineas": [{"producto_id": 1, "cantidad": 1}]}).json()
    vencido = cliente.post(f"/ordenes/{cupon['id']}/cupon", headers=como(1), json={"codigo": "VENCIDO5"})
    assert vencido.status_code == 422
    assert vencido.json()["title"] == "Cupón inválido" and vencido.json()["detail"] == "El cupón está vencido"
    assert vencido.headers["content-type"].startswith("application/problem+json")


def test_ruta_inexistente_es_404_rfc_7807(cliente):
    r = cliente.get("/no-existe")
    assert r.status_code == 404 and r.json()["codigo"] == "RUTA_NO_ENCONTRADA"


def test_swagger_documenta_400_y_no_el_422_generico(cliente):
    esquema = cliente.get("/openapi.json").json()
    crear = esquema["paths"]["/ordenes"]["post"]["responses"]
    assert {"201", "400", "401", "404", "409", "422"} <= set(crear)
    assert "application/problem+json" in crear["400"]["content"]
    assert "HTTPValidationError" not in str(esquema)
    for ruta in esquema["paths"].values():
        for operacion in ruta.values():
            respuesta_422 = operacion.get("responses", {}).get("422")
            assert respuesta_422 is None or "Validation Error" not in respuesta_422["description"]


def test_api_docs_lleva_a_swagger(cliente):
    r = cliente.get("/api-docs", follow_redirects=False)
    assert r.status_code in (302, 307) and r.headers["location"] == "/docs"
