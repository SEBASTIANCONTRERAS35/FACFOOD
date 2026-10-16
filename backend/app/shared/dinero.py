"""El dinero viaja en la API como texto con 2 decimales ("65.08"), nunca como float."""

from decimal import ROUND_HALF_UP, Decimal

CENTAVO = Decimal("0.01")


def a_texto(monto: Decimal) -> str:
    return f"{Decimal(str(monto)).quantize(CENTAVO, rounding=ROUND_HALF_UP):.2f}"
