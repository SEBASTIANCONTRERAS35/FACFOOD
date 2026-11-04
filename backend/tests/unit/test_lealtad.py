import pytest

from app.domain.crm.retencion import nivel_lealtad, siguiente_nivel


@pytest.mark.parametrize("pedidos, esperado", [
    (0, ("plata", 3, 3)), (2, ("plata", 3, 1)), (3, ("oro", 10, 7)), (9, ("oro", 10, 1)), (10, None), (25, None),
])
def test_siguiente_nivel(pedidos, esperado):
    assert siguiente_nivel(pedidos) == esperado


def test_los_umbrales_no_cambiaron():
    assert [nivel_lealtad(p) for p in (0, 2, 3, 9, 10)] == ["bronce", "bronce", "plata", "plata", "oro"]
