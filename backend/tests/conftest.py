import pytest
from fastapi.testclient import TestClient

from app.adapters.memoria.uow import AlmacenMemoria, UnidadDeTrabajoMemoria
from app.main import create_app
from app.seed import cargar_datos_ejemplo
from app.shared.uow import obtener_fabrica_uow


@pytest.fixture
def fabrica():
    """Almacén en memoria nuevo, con los datos de ejemplo, para cada prueba."""
    almacen = AlmacenMemoria()
    f = lambda: UnidadDeTrabajoMemoria(almacen)  # noqa: E731
    cargar_datos_ejemplo(f)
    return f


@pytest.fixture
def cliente(fabrica):
    app = create_app()
    app.dependency_overrides[obtener_fabrica_uow] = lambda: fabrica
    return TestClient(app)


def como(usuario_id: int) -> dict:
    """Encabezado para actuar como un usuario de ejemplo (solo desarrollo)."""
    return {"X-Usuario-Id": str(usuario_id)}
