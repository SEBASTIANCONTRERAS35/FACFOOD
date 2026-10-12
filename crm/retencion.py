"""
Capa de Dominio - FACFOOD
Módulo CRM: retención de usuarios (cupones y lealtad)

Dominio puro: no depende de base de datos ni de frameworks.

Reglas de negocio:
- Cupón: porcentaje de descuento con vigencia, pedido mínimo, tope de
  descuento y número máximo de usos.
- Lealtad: el nivel (bronce, plata, oro) depende de los pedidos
  completados del usuario y da un porcentaje fijo de descuento.
- Los descuentos NO se acumulan: se aplica el mayor entre cupón y lealtad.
- Cupón de bienvenida: solo para quien aún no ha completado ningún pedido.
"""

from datetime import date, timedelta


class CuponInvalidoError(Exception):
    """Se lanza cuando un cupón no se puede aplicar (vencido, agotado, etc.)."""


class Cupon:
    def __init__(
        self,
        codigo: str,
        porcentaje: float,
        vigente_hasta: date,
        pedido_minimo: float = 0.0,
        tope_descuento: float | None = None,
        usos_maximos: int = 1,
    ):
        if not 0 < porcentaje <= 100:
            raise ValueError("El porcentaje debe estar entre 0 (sin incluir) y 100")
        self.codigo = codigo
        self.porcentaje = porcentaje
        self.vigente_hasta = vigente_hasta
        self.pedido_minimo = pedido_minimo
        self.tope_descuento = tope_descuento
        self.usos_maximos = usos_maximos
        self.usos_actuales = 0

    def calcular_descuento(self, subtotal: float, hoy: date) -> float:
        if hoy > self.vigente_hasta:
            raise CuponInvalidoError("El cupón está vencido")
        if self.usos_actuales >= self.usos_maximos:
            raise CuponInvalidoError("El cupón ya alcanzó su límite de usos")
        if subtotal < self.pedido_minimo:
            raise CuponInvalidoError(
                f"El pedido mínimo para este cupón es ${self.pedido_minimo:.2f}"
            )

        descuento = subtotal * self.porcentaje / 100
        if self.tope_descuento is not None:
            descuento = min(descuento, self.tope_descuento)
        return round(descuento, 2)

    def registrar_uso(self) -> None:
        self.usos_actuales += 1


# ---- Lealtad ----
DESCUENTO_POR_NIVEL = {"bronce": 0, "plata": 5, "oro": 10}


def nivel_lealtad(pedidos_completados: int) -> str:
    if pedidos_completados >= 10:
        return "oro"
    if pedidos_completados >= 3:
        return "plata"
    return "bronce"


def descuento_lealtad(subtotal: float, pedidos_completados: int) -> float:
    porcentaje = DESCUENTO_POR_NIVEL[nivel_lealtad(pedidos_completados)]
    return round(subtotal * porcentaje / 100, 2)


# ---- Reglas combinadas ----
def mejor_descuento(
    subtotal: float,
    pedidos_completados: int,
    hoy: date,
    cupon: Cupon | None = None,
) -> float:
    """Devuelve el mayor descuento entre lealtad y cupón (no se acumulan)."""
    por_lealtad = descuento_lealtad(subtotal, pedidos_completados)
    por_cupon = cupon.calcular_descuento(subtotal, hoy) if cupon else 0.0
    return max(por_lealtad, por_cupon)


def cupon_bienvenida(pedidos_completados: int, hoy: date) -> Cupon | None:
    """15% (tope $30) válido 30 días, solo para quien no ha hecho pedidos."""
    if pedidos_completados > 0:
        return None
    return Cupon(
        codigo="BIENVENIDA15",
        porcentaje=15,
        vigente_hasta=hoy + timedelta(days=30),
        tope_descuento=30.0,
        usos_maximos=1,
    )
