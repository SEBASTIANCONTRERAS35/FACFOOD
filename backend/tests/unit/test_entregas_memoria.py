from datetime import datetime, timezone

import pytest

from app.ports.repositorios import EntregaRegistro
from app.shared.errores import Conflicto

def test_repo_memoria_filtra_por_modalidad_estado_y_asignacion(fabrica):
    with fabrica() as uow:
        assert [r.id for r in uow.entregas.ordenes_disponibles()] == [1, 3]
        uow.entregas.agregar(EntregaRegistro(None, 1, 5, "ACEPTADA", datetime.now(timezone.utc)))
        uow.commit()
    with fabrica() as uow:
        assert [r.id for r in uow.entregas.ordenes_disponibles()] == [3]

def test_repo_memoria_rechaza_una_segunda_asignacion(fabrica):
    with fabrica() as uow:
        uow.entregas.agregar(EntregaRegistro(None, 1, 5, "ACEPTADA", datetime.now(timezone.utc)))
        with pytest.raises(Conflicto):
            uow.entregas.agregar(EntregaRegistro(None, 1, 5, "ACEPTADA", datetime.now(timezone.utc)))
