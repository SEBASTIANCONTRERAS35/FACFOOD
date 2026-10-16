"""Datos de ejemplo de FACFOOD (puestos de CU, usuarios, cupones y órdenes).

- Modo memoria: se cargan solos al arrancar la API.
- Modo postgres: `python -m app.seed` después de `alembic upgrade head`.
Es idempotente: si ya hay usuarios, no hace nada.

Las coordenadas son aproximadas, solo para la demo.
Contraseña de todos los usuarios de ejemplo: facfood123
"""

from datetime import date, datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from functools import lru_cache

from app.domain.crm.retencion import Cupon
from app.domain.entrega import EntregaEstudiante
from app.domain.erp.orden import EstadoOrden, Orden
from app.domain.usuario import Usuario
from app.ports.repositorios import (
    CuentaUsuario,
    CuponRegistro,
    Destino,
    EventoOrden,
    FacturaRegistro,
    OrdenRegistro,
    Producto,
    PuntoVenta,
)

PASSWORD_EJEMPLO = "facfood123"
RFC_PUBLICO_EN_GENERAL = "XAXX010101000"

USUARIOS = [
    # correo, nombre, credencial, rol, pedidos_completados
    ("diana@facfood.mx", "Diana Romero", "319000001", "comprador", 0),
    ("sebastian@facfood.mx", "Sebastián Contreras", "319000002", "comprador", 3),
    ("memo@facfood.mx", "Guillermo «Don Memo» Pérez", "319000003", "vendedor", 5),
    ("lupita@facfood.mx", "Guadalupe «Lupita» Sánchez", "319000004", "vendedor", 4),
    ("arturo@facfood.mx", "Arturo Ciriaco", "319000005", "repartidor", 0),
]

DESTINOS = [
    ("Facultad de Ingeniería", 19.3311, -99.1839),
    ("Facultad de Arquitectura", 19.3313, -99.1879),
    ("Biblioteca Central", 19.3341, -99.1871),
    ("Facultad de Filosofía y Letras", 19.3346, -99.1856),
    ("Facultad de Medicina", 19.3328, -99.1810),
    ("Facultad de Contaduría y Administración", 19.3246, -99.1849),
    ("Facultad de Ciencias", 19.3246, -99.1792),
]

# nombre, categoria, descripcion, ubicacion, lat, lon, calif, reseñas, cierre, abierto, entrega, vendedor(correo), productos
PUNTOS = [
    ("Tacos Don Memo", "Tacos", "Tacos al pastor y de suadero hechos al momento.",
     "Frente a la Facultad de Ingeniería", 19.3320, -99.1832, "4.8", 126, "17:00", True, True, "memo@facfood.mx",
     [("Taco de pastor", "Con piña, cebolla y cilantro", "18.00"),
      ("Taco de suadero", "Tortilla doble, salsa verde", "18.00"),
      ("Quesadilla de queso", "Tortilla de maíz hecha a mano", "30.00"),
      ("Gringa de pastor", "Tortilla de harina y queso", "45.00"),
      ("Agua de jamaica", "Vaso de 500 ml", "15.00")]),
    ("Café Ingeniería", "Café", "Café de olla, americano y pan dulce.",
     "Junto al Anexo de Ingeniería", 19.3302, -99.1846, "4.6", 88, "19:00", True, False, None,
     [("Café americano", "Vaso de 355 ml", "22.00"),
      ("Café de olla", "Con canela y piloncillo", "25.00"),
      ("Concha", "Vainilla o chocolate", "14.00"),
      ("Cuernito con jamón", "Recién horneado", "35.00")]),
    ("Chilaquiles Lupita", "Desayunos", "Chilaquiles rojos y verdes con todo.",
     "Entre Ingeniería y Arquitectura", 19.3335, -99.1858, "4.9", 203, "13:00", True, True, "lupita@facfood.mx",
     [("Chilaquiles verdes", "Con crema, queso y cebolla", "55.00"),
      ("Chilaquiles rojos con pollo", "Pollo deshebrado", "70.00"),
      ("Torta de chilaquil", "El clásico de CU", "50.00"),
      ("Jugo de naranja", "Natural, 500 ml", "25.00")]),
    ("Tortas El Güero", "Tortas", "Tortas de milanesa, pierna y cubana.",
     "Estacionamiento de Ingeniería", 19.3289, -99.1829, "4.5", 64, "16:00", True, True, None,
     [("Torta de milanesa", "Con aguacate y quesillo", "60.00"),
      ("Torta cubana", "Para los de mucha hambre", "80.00"),
      ("Refresco", "Lata de 355 ml", "20.00")]),
    ("Comida Corrida Doña Mary", "Comida corrida", "Sopa, guisado del día, arroz y agua.",
     "Cerca de la Facultad de Medicina", 19.3348, -99.1820, "4.7", 141, "16:30", True, True, None,
     [("Menú del día", "Sopa, arroz, guisado y agua", "75.00"),
      ("Guisado extra", "Pregunta por el del día", "35.00")]),
    ("Postres La Abuela", "Postres", "Pasteles y gelatinas caseras.",
     "Camino a Arquitectura", 19.3297, -99.1866, "4.8", 57, "18:00", True, True, None,
     [("Rebanada de pastel de chocolate", "Receta de la abuela", "40.00"),
      ("Gelatina de mosaico", "Vaso individual", "20.00"),
      ("Flan napolitano", "Con cajeta", "30.00")]),
    ("Jugos Frida", "Bebidas", "Jugos, licuados y aguas frescas.",
     "Frente a la Biblioteca Central", 19.3325, -99.1873, "4.4", 39, "17:30", True, False, None,
     [("Licuado de plátano", "Con leche, 500 ml", "35.00"),
      ("Agua de horchata", "Vaso de 500 ml", "18.00")]),
    ("Quesadillas Las Islas", "Antojitos", "Quesadillas de comal con guisados.",
     "Junto a Las Islas", 19.3342, -99.1867, "4.6", 72, "15:00", False, True, None,
     [("Quesadilla de flor de calabaza", "Comal, tortilla azul", "35.00"),
      ("Quesadilla de chicharrón", "Con salsa roja", "35.00")]),
]

CUPONES = [
    # codigo, %, vigente_hasta, minimo, tope, usos_maximos, solo_primer_pedido, uno_por_usuario
    ("BIENVENIDA15", 15, date(2027, 12, 31), 0, 30, 100_000, True, True),
    ("PROMO10", 10, date(2027, 6, 30), 100, None, 500, False, True),
    ("UNICO20", 20, date(2027, 12, 31), 0, None, 1, False, False),
    ("VENCIDO5", 5, date(2026, 1, 1), 0, None, 100, False, False),
]


@lru_cache
def _hash_ejemplo() -> bytes:
    # bcrypt es lento a propósito; se calcula una sola vez para todos los usuarios de ejemplo.
    u = Usuario("ejemplo", "000000000", consentimiento_datos=True)
    u.registrar_password(PASSWORD_EJEMPLO)
    return u.password_hash


def _centavos(x: Decimal) -> Decimal:
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def cargar_datos_ejemplo(fabrica) -> bool:
    """Carga los datos si la base está vacía. Devuelve True si cargó algo."""
    with fabrica() as uow:
        if uow.usuarios.listar():
            return False

        usuarios = {}
        for correo, nombre, credencial, rol, pedidos in USUARIOS:
            u = Usuario.restaurar(nombre, credencial, _hash_ejemplo(), rol, pedidos)
            usuarios[correo] = uow.usuarios.agregar(CuentaUsuario(None, correo, u))

        destinos = {n: uow.destinos.agregar(Destino(0, n, la, lo)) for n, la, lo in DESTINOS}

        puntos, productos = {}, {}
        for (nombre, cat, desc, ubic, la, lo, calif, res, cierre, abierto, entrega, vendedor, prods) in PUNTOS:
            p = uow.puntos_venta.agregar(PuntoVenta(
                0, usuarios[vendedor].id if vendedor else None, nombre, cat, desc, ubic, la, lo,
                Decimal(calif), res, cierre, abierto, entrega,
            ))
            puntos[nombre] = p
            for pn, pd, precio in prods:
                productos[(nombre, pn)] = uow.productos.agregar(Producto(0, p.id, pn, pd, Decimal(precio), True))

        for codigo, pct, hasta, minimo, tope, usos, primero, uno in CUPONES:
            uow.cupones.agregar(CuponRegistro(
                None, Cupon(codigo, pct, hasta, minimo, tope, usos), primero, uno,
            ))

        _ordenes_de_ejemplo(uow, usuarios, puntos, productos, destinos)
        uow.commit()
        return True


def _ordenes_de_ejemplo(uow, usuarios, puntos, productos, destinos):
    """Órdenes ya pagadas para que las vistas 05–08 tengan datos sin pasar por el checkout."""
    ahora = datetime.now(timezone.utc).replace(microsecond=0)
    hoy = date.today()
    ejemplos = [
        # comprador, puesto, [(producto, cantidad)], destino (None = pickup), estado final, código, minutos atrás
        ("diana@facfood.mx", "Tacos Don Memo", [("Taco de suadero", 3), ("Agua de jamaica", 1)],
         "Facultad de Arquitectura", EstadoOrden.PAGADA, "4821", 12),
        ("sebastian@facfood.mx", "Tacos Don Memo", [("Taco de pastor", 2), ("Quesadilla de queso", 1)],
         None, EstadoOrden.EN_PREPARACION, None, 20),
        ("diana@facfood.mx", "Chilaquiles Lupita", [("Chilaquiles verdes", 1), ("Jugo de naranja", 1)],
         "Biblioteca Central", EstadoOrden.PAGADA, "7305", 8),
        ("sebastian@facfood.mx", "Café Ingeniería", [("Café americano", 1), ("Concha", 2)],
         None, EstadoOrden.ENTREGADA, None, 180),
    ]
    camino = [EstadoOrden.PAGADA, EstadoOrden.EN_PREPARACION, EstadoOrden.ENVIADA, EstadoOrden.ENTREGADA]

    for correo, puesto, lineas, destino, estado_final, codigo, minutos in ejemplos:
        punto = puntos[puesto]
        catalogo = {str(p.id): p.precio for (n, _), p in productos.items() if n == puesto}
        orden = Orden(catalogo, hoy)
        for prod, cant in lineas:
            orden.agregar_linea(str(productos[(puesto, prod)].id), cant)

        distancia_km = Decimal("0")
        destino_id = None
        if destino:
            d = destinos[destino]
            destino_id = d.id
            distancia_km = _centavos(Decimal(uow.puntos_venta.distancia_m(punto.id, d.lat, d.lon)) / 1000)
            orden.definir_envio(_centavos(distancia_km * Decimal(str(EntregaEstudiante.COSTO_POR_KM))))

        inicio = ahora - timedelta(minutes=minutos)
        momentos = [(EstadoOrden.CREADA, inicio)]
        factura = None
        for i, estado in enumerate(camino[: camino.index(estado_final) + 1]):
            orden.avanzar_estado(estado)
            momentos.append((estado, inicio + timedelta(minutes=1 + 3 * i)))
            if estado is EstadoOrden.PAGADA:
                factura = orden.generar_factura(RFC_PUBLICO_EN_GENERAL)

        registro = uow.ordenes.agregar(OrdenRegistro(
            None, usuarios[correo].id, punto.id, orden,
            "estudiante" if destino else "pickup", destino_id, distancia_km,
            pedidos_completados_al_crear=usuarios[correo].usuario.pedidos_completados,
            codigo_entrega=codigo, creada_en=inicio,
        ))
        for estado, cuando in momentos:
            uow.eventos.agregar(EventoOrden(registro.id, estado.value, cuando))
        uow.facturas.agregar(FacturaRegistro(registro.id, factura, momentos[1][1]))


if __name__ == "__main__":
    from app.shared.uow import obtener_fabrica_uow

    cargo = cargar_datos_ejemplo(obtener_fabrica_uow())
    print("Datos de ejemplo cargados." if cargo else "La base ya tenía datos; no se cargó nada.")
