from tests.conftest import como


def test_salud(cliente):
    assert cliente.get("/salud").json()["estado"] == "ok"


def test_usuarios_de_prueba_para_el_selector(cliente):
    roles = {u["rol"] for u in cliente.get("/dev/usuarios").json()}
    assert roles == {"comprador", "vendedor", "repartidor"}


def test_las_ordenes_de_ejemplo_traen_eventos_y_factura(fabrica):
    with fabrica() as uow:
        pagadas = [uow.ordenes.por_id(i) for i in range(1, 5)]
        assert all(uow.facturas.de_orden(r.id) is not None for r in pagadas)
        assert [e.estado for e in uow.eventos.de_orden(4)] == [
            "CREADA", "PAGADA", "EN_PREPARACION", "ENVIADA", "ENTREGADA",
        ]


def test_la_transaccion_sin_commit_se_revierte(fabrica):
    with fabrica() as uow:
        uow.puntos_venta.cambiar_abierto(1, False)
    with fabrica() as uow:
        assert uow.puntos_venta.por_id(1).abierto is True


def test_usuario_de_prueba_desconocido_no_autentica(cliente):
    # No hay endpoints protegidos todavía; se prueba la dependencia directamente.
    from fastapi import Depends, FastAPI
    from fastapi.testclient import TestClient

    from app.shared.auth import UsuarioActual, get_usuario_actual
    from app.shared.errores import registrar_manejadores
    from app.shared.uow import obtener_fabrica_uow

    app = FastAPI()
    registrar_manejadores(app)
    app.dependency_overrides[obtener_fabrica_uow] = cliente.app.dependency_overrides[obtener_fabrica_uow]

    @app.get("/yo")
    def yo(u: UsuarioActual = Depends(get_usuario_actual)):
        return {"id": u.id, "rol": u.rol}

    c = TestClient(app)
    assert c.get("/yo", headers=como(5)).json() == {"id": 5, "rol": "repartidor"}
    assert c.get("/yo", headers=como(999)).status_code == 401
    assert c.get("/yo").status_code == 401
