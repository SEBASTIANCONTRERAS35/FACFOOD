"""Casos de uso del checkout (vista 04): crear la orden, cupón, entrega y pago.

Lleva la orden de CREADA a PAGADA. De PAGADA en adelante es de la rebanada de Arturo.
"""

import secrets
from datetime import date, datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from app.domain.crm.retencion import DESCUENTO_POR_NIVEL, CuponInvalidoError, nivel_lealtad, siguiente_nivel
from app.domain.entrega import EntregaEstudiante, Pickup
from app.domain.erp.orden import EstadoOrden, Orden
from app.ports.repositorios import EventoOrden, FacturaRegistro, OrdenRegistro, UnidadDeTrabajo
from app.shared.auth import UsuarioActual
from app.shared.errores import Conflicto, DatosInvalidos, NoEncontrado
from app.shared.dinero import a_texto
from app.shared.presentacion import orden_a_json
from app.shared.uow import FabricaUoW

RFC_PUBLICO_EN_GENERAL = "XAXX010101000"


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


def _orden_propia(uow: UnidadDeTrabajo, orden_id: int, actual: UsuarioActual, bloquear=False) -> OrdenRegistro:
    registro = uow.ordenes.por_id(orden_id, bloquear=bloquear)
    # A otro usuario se le responde igual que si no existiera: no se revelan órdenes ajenas.
    if registro is None or registro.comprador_id != actual.id:
        raise NoEncontrado("Esa orden no existe")
    return registro


def _punto_abierto(uow: UnidadDeTrabajo, punto_id: int):
    punto = uow.puntos_venta.por_id(punto_id)
    if punto is None:
        raise NoEncontrado("Ese puesto no existe")
    if not punto.abierto:
        raise Conflicto(f"{punto.nombre} está cerrado en este momento", "PUESTO_CERRADO")
    return punto


def _definir_entrega(uow: UnidadDeTrabajo, registro: OrdenRegistro, punto, metodo: str, destino_id: int | None):
    if metodo == "pickup":
        registro.orden.definir_entrega(Pickup())
        registro.metodo_entrega, registro.destino_id, registro.distancia_km = "pickup", None, Decimal("0")
        return
    if not punto.admite_entrega:
        raise DatosInvalidos(f"{punto.nombre} solo ofrece pickup", "SIN_ENTREGA")
    if destino_id is None:
        raise DatosInvalidos("Elige a dónde te lo llevamos", "DESTINO_REQUERIDO")
    destino = uow.destinos.por_id(destino_id)
    if destino is None:
        raise NoEncontrado("Ese destino no existe")
    metros = uow.puntos_venta.distancia_m(punto.id, destino.lat, destino.lon)  # PostGIS en producción
    km = (Decimal(metros) / 1000).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    registro.orden.definir_entrega(EntregaEstudiante(), km)
    registro.metodo_entrega, registro.destino_id, registro.distancia_km = "estudiante", destino.id, km


def _validar_cupon_para(uow: UnidadDeTrabajo, cupon_reg, actual: UsuarioActual, pedidos_completados: int):
    if cupon_reg.solo_primer_pedido and pedidos_completados > 0:
        raise CuponInvalidoError("Este cupón es solo para tu primer pedido")
    if cupon_reg.uno_por_usuario and uow.cupones.usos_de_usuario(cupon_reg.id, actual.id) > 0:
        raise CuponInvalidoError("Ya usaste este cupón")


# Los pedidos CREADA (carritos que no se pagaron) y CANCELADA no son pedidos para el usuario.
ESTADOS_VISIBLES = {EstadoOrden.PAGADA, EstadoOrden.EN_PREPARACION, EstadoOrden.ENVIADA, EstadoOrden.ENTREGADA}


def mis_ordenes(fabrica: FabricaUoW, actual: UsuarioActual) -> list[dict]:
    with fabrica() as uow:
        resultado = []
        # El filtro va en la consulta: si se filtrara después del límite, muchos carritos
        # abandonados (CREADA) desplazarían a los pedidos reales fuera de la lista.
        for r in uow.ordenes.de_comprador(actual.id, estados={e.value for e in ESTADOS_VISIBLES}):
            punto = uow.puntos_venta.por_id(r.punto_venta_id)
            resultado.append({
                "id": r.id, "estado": r.orden.estado.value,
                "punto_venta": {"id": punto.id, "nombre": punto.nombre},
                "metodo_entrega": r.metodo_entrega,
                "piezas": sum(l.cantidad for l in r.orden.lineas),
                "total": a_texto(r.orden.total),
                "creada_en": r.creada_en.isoformat() if r.creada_en else None,
            })
        return resultado


def cupones_del_usuario(fabrica: FabricaUoW, actual: UsuarioActual, hoy: date | None = None) -> dict:
    """Nivel de lealtad y cupones que el usuario puede usar hoy (o que ya usó)."""
    hoy = hoy or date.today()
    with fabrica() as uow:
        pedidos = uow.usuarios.por_id(actual.id).usuario.pedidos_completados
        cupones = []
        for reg in uow.cupones.listar():
            c = reg.cupon
            agotado = c.usos_actuales >= c.usos_maximos
            ya_lo_uso = uow.cupones.usos_de_usuario(reg.id, actual.id) > 0
            if ya_lo_uso and (reg.uno_por_usuario or agotado):
                estado = "usado"
            elif hoy > c.vigente_hasta or agotado:
                continue  # vencido o agotado: no se muestra
            elif reg.solo_primer_pedido and pedidos > 0:
                continue  # el de bienvenida solo es para quien no ha completado pedidos
            else:
                estado = "disponible"
            cupones.append({
                "codigo": c.codigo, "porcentaje": float(c.porcentaje),
                "pedido_minimo": a_texto(Decimal(str(c.pedido_minimo))),
                "tope_descuento": a_texto(Decimal(str(c.tope_descuento))) if c.tope_descuento is not None else None,
                "vigente_hasta": c.vigente_hasta.isoformat(),
                "solo_primer_pedido": reg.solo_primer_pedido, "uno_por_usuario": reg.uno_por_usuario,
                "estado": estado,
            })
    cupones.sort(key=lambda x: (x["estado"] != "disponible", -x["porcentaje"]))
    nivel = nivel_lealtad(pedidos)
    siguiente = siguiente_nivel(pedidos)
    return {
        "lealtad": {
            "nivel": nivel, "descuento_pct": DESCUENTO_POR_NIVEL[nivel], "pedidos_completados": pedidos,
            "siguiente": None if siguiente is None else {
                "nivel": siguiente[0], "pedidos": siguiente[1], "faltan": siguiente[2],
                "descuento_pct": DESCUENTO_POR_NIVEL[siguiente[0]],
            },
        },
        "cupones": cupones,
    }


def destinos(fabrica: FabricaUoW) -> list[dict]:
    with fabrica() as uow:
        return [{"id": d.id, "nombre": d.nombre} for d in uow.destinos.listar()]


def crear_orden(fabrica: FabricaUoW, actual: UsuarioActual, punto_venta_id: int,
                lineas: list[tuple[int, int]], metodo: str, destino_id: int | None) -> dict:
    with fabrica() as uow:
        cuenta = uow.usuarios.por_id(actual.id)
        punto = _punto_abierto(uow, punto_venta_id)
        # Solo productos de este puesto y disponibles; el precio sale de aquí, nunca del cliente.
        catalogo = {str(p.id): p.precio for p in uow.productos.de_punto(punto.id) if p.disponible}
        orden = Orden(catalogo, date.today())
        cantidades: dict[int, int] = {}
        for producto_id, cantidad in lineas:
            cantidades[producto_id] = cantidades.get(producto_id, 0) + cantidad
        for producto_id, cantidad in cantidades.items():
            orden.agregar_linea(str(producto_id), cantidad)
        orden.definir_lealtad(cuenta.usuario.pedidos_completados)

        registro = OrdenRegistro(
            None, actual.id, punto.id, orden, "pickup",
            pedidos_completados_al_crear=cuenta.usuario.pedidos_completados,
        )
        _definir_entrega(uow, registro, punto, metodo, destino_id)
        registro = uow.ordenes.agregar(registro)
        uow.eventos.agregar(EventoOrden(registro.id, EstadoOrden.CREADA.value, _ahora(), actual.id))
        respuesta = orden_a_json(uow, registro, actual.id)
        uow.commit()
        return respuesta


def cambiar_entrega(fabrica: FabricaUoW, actual: UsuarioActual, orden_id: int, metodo: str,
                    destino_id: int | None) -> dict:
    with fabrica() as uow:
        registro = _orden_propia(uow, orden_id, actual)
        _definir_entrega(uow, registro, uow.puntos_venta.por_id(registro.punto_venta_id), metodo, destino_id)
        uow.ordenes.guardar(registro)
        respuesta = orden_a_json(uow, registro, actual.id)
        uow.commit()
        return respuesta


def aplicar_cupon(fabrica: FabricaUoW, actual: UsuarioActual, orden_id: int, codigo: str) -> dict:
    with fabrica() as uow:
        registro = _orden_propia(uow, orden_id, actual)
        cupon_reg = uow.cupones.por_codigo(codigo)
        if cupon_reg is None:
            raise NoEncontrado("Ese cupón no existe", "CUPON_INEXISTENTE")
        _validar_cupon_para(uow, cupon_reg, actual, registro.pedidos_completados_al_crear)
        registro.orden.aplicar_cupon(cupon_reg.cupon)  # vencido, agotado o bajo el mínimo -> 422
        registro.cupon_id = cupon_reg.id
        uow.ordenes.guardar(registro)
        respuesta = orden_a_json(uow, registro, actual.id)
        uow.commit()
        return respuesta


def quitar_cupon(fabrica: FabricaUoW, actual: UsuarioActual, orden_id: int) -> dict:
    with fabrica() as uow:
        registro = _orden_propia(uow, orden_id, actual)
        registro.orden.quitar_cupon()
        registro.cupon_id = None
        uow.ordenes.guardar(registro)
        respuesta = orden_a_json(uow, registro, actual.id)
        uow.commit()
        return respuesta


def pagar(fabrica: FabricaUoW, actual: UsuarioActual, orden_id: int, rfc: str | None) -> dict:
    """Pago simulado. Todo en una transacción: si algo falla, la orden sigue CREADA."""
    with fabrica() as uow:
        registro = _orden_propia(uow, orden_id, actual, bloquear=True)  # evita pagar dos veces
        if registro.orden.estado is not EstadoOrden.CREADA:
            raise Conflicto("Esta orden ya fue pagada", "ORDEN_YA_PAGADA")
        _punto_abierto(uow, registro.punto_venta_id)
        orden = registro.orden
        cuenta = uow.usuarios.por_id(actual.id)
        orden.definir_lealtad(cuenta.usuario.pedidos_completados)

        cupon_reg = None
        if registro.cupon_id is not None:
            # Bloquea la fila del cupón: dos pagos simultáneos con el mismo cupón se forman en fila,
            # y el segundo ve los usos ya actualizados (concurrencia tipo "Hot Sale").
            cupon_reg = uow.cupones.por_id(registro.cupon_id, bloquear=True)
            _validar_cupon_para(uow, cupon_reg, actual, cuenta.usuario.pedidos_completados)
            orden.aplicar_cupon(cupon_reg.cupon)

        orden.avanzar_estado(EstadoOrden.PAGADA)  # revalida el cupón y lo consume si ganó
        if cupon_reg is not None and orden.origen_descuento == "cupon":
            uow.cupones.guardar(cupon_reg)
            uow.cupones.registrar_uso(cupon_reg.id, actual.id, registro.id)

        factura = orden.generar_factura((rfc or RFC_PUBLICO_EN_GENERAL).strip())
        if registro.metodo_entrega == "estudiante":
            registro.codigo_entrega = f"{secrets.randbelow(10_000):04d}"
        registro.pedidos_completados_al_crear = cuenta.usuario.pedidos_completados

        ahora = _ahora()
        uow.ordenes.guardar(registro)
        uow.eventos.agregar(EventoOrden(registro.id, EstadoOrden.PAGADA.value, ahora, actual.id))
        uow.facturas.agregar(FacturaRegistro(registro.id, factura, ahora))
        respuesta = orden_a_json(uow, registro, actual.id)
        uow.commit()
        return respuesta
