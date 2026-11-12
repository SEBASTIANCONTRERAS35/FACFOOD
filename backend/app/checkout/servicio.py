"""Casos de uso del checkout (vista 04): crear la orden, cupón, entrega y pago.

Lleva la orden de CREADA a PAGADA. De PAGADA en adelante es de la rebanada de Arturo.
"""

import logging
import secrets
from datetime import date, datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal

from app.domain.crm.retencion import DESCUENTO_POR_NIVEL, CuponInvalidoError, nivel_lealtad, siguiente_nivel
from app.domain.entrega import EntregaEstudiante, Pickup
from app.domain.erp.orden import EstadoOrden, Orden
from app.ports.pagos import EventoDePago, PagoRegistro, PasarelaDePago, PasarelaNoDisponible
from app.ports.repositorios import EventoOrden, FacturaRegistro, OrdenRegistro, UnidadDeTrabajo
from app.shared.auth import UsuarioActual
from app.shared.errores import Conflicto, DatosInvalidos, NoEncontrado, ServicioNoDisponible
from app.shared.dinero import a_texto
from app.shared.presentacion import orden_a_json
from app.shared.uow import FabricaUoW

RFC_PUBLICO_EN_GENERAL = "XAXX010101000"
# Stripe exige al menos 30 minutos para que una sesión de Checkout expire.
VIGENCIA_PAGO = timedelta(minutes=30)

log = logging.getLogger(__name__)


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


def _sin_pago_en_curso(uow: UnidadDeTrabajo, orden_id: int) -> None:
    """Mientras hay un cobro abierto en la pasarela, el monto no puede cambiar."""
    if uow.pagos.pendiente_de_orden(orden_id) is not None:
        raise Conflicto("Tienes un pago en curso. Cancélalo para modificar el pedido", "PAGO_EN_CURSO")


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
        _sin_pago_en_curso(uow, orden_id)
        _definir_entrega(uow, registro, uow.puntos_venta.por_id(registro.punto_venta_id), metodo, destino_id)
        uow.ordenes.guardar(registro)
        respuesta = orden_a_json(uow, registro, actual.id)
        uow.commit()
        return respuesta


def aplicar_cupon(fabrica: FabricaUoW, actual: UsuarioActual, orden_id: int, codigo: str) -> dict:
    with fabrica() as uow:
        registro = _orden_propia(uow, orden_id, actual)
        _sin_pago_en_curso(uow, orden_id)
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
        _sin_pago_en_curso(uow, orden_id)
        registro.orden.quitar_cupon()
        registro.cupon_id = None
        uow.ordenes.guardar(registro)
        respuesta = orden_a_json(uow, registro, actual.id)
        uow.commit()
        return respuesta


def _preparar_cobro(uow: UnidadDeTrabajo, registro: OrdenRegistro, actual: UsuarioActual):
    """Fija el monto a cobrar con las reglas vigentes: puesto abierto, lealtad actual y cupón
    revalidado. Devuelve (cuenta, cupón bloqueado o None)."""
    if registro.orden.estado is not EstadoOrden.CREADA:
        raise Conflicto("Esta orden ya fue pagada", "ORDEN_YA_PAGADA")
    _punto_abierto(uow, registro.punto_venta_id)
    cuenta = uow.usuarios.por_id(registro.comprador_id)
    registro.orden.definir_lealtad(cuenta.usuario.pedidos_completados)
    cupon_reg = None
    if registro.cupon_id is not None:
        # Bloquea la fila del cupón: dos pagos simultáneos con el mismo cupón se forman en fila,
        # y el segundo ve los usos ya actualizados (concurrencia tipo "Hot Sale").
        cupon_reg = uow.cupones.por_id(registro.cupon_id, bloquear=True)
        _validar_cupon_para(uow, cupon_reg, actual, cuenta.usuario.pedidos_completados)
        registro.orden.aplicar_cupon(cupon_reg.cupon)
    return cuenta, cupon_reg


def _cerrar_como_pagada(uow: UnidadDeTrabajo, registro: OrdenRegistro, cuenta, cupon_reg, consumido: bool,
                        rfc: str | None) -> None:
    """Lo que pasa al quedar PAGADA, venga del pago simulado o del aviso de la pasarela."""
    orden = registro.orden
    if cupon_reg is not None and orden.origen_descuento == "cupon":
        if consumido:
            uow.cupones.guardar(cupon_reg)
        uow.cupones.registrar_uso(cupon_reg.id, registro.comprador_id, registro.id)
    factura = orden.generar_factura((rfc or RFC_PUBLICO_EN_GENERAL).strip())
    if registro.metodo_entrega == "estudiante":
        registro.codigo_entrega = f"{secrets.randbelow(10_000):04d}"
    registro.pedidos_completados_al_crear = cuenta.usuario.pedidos_completados
    ahora = _ahora()
    uow.ordenes.guardar(registro)
    uow.eventos.agregar(EventoOrden(registro.id, EstadoOrden.PAGADA.value, ahora, registro.comprador_id))
    uow.facturas.agregar(FacturaRegistro(registro.id, factura, ahora))


def pagar(fabrica: FabricaUoW, actual: UsuarioActual, orden_id: int, rfc: str | None,
          pasarela: PasarelaDePago | None = None) -> dict:
    """Pago simulado. Todo en una transacción: si algo falla, la orden sigue CREADA."""
    if pasarela is not None and pasarela.redirige:
        # Con una pasarela real, este atajo dejaría marcar como pagada una orden sin cobrarla.
        raise Conflicto("Esta orden se paga con tarjeta desde el checkout", "PAGO_EN_LINEA_REQUERIDO")
    with fabrica() as uow:
        registro = _orden_propia(uow, orden_id, actual, bloquear=True)  # evita pagar dos veces
        cuenta, cupon_reg = _preparar_cobro(uow, registro, actual)
        _sin_pago_en_curso(uow, orden_id)
        orden = registro.orden
        usos_antes = cupon_reg.cupon.usos_actuales if cupon_reg else 0
        orden.avanzar_estado(EstadoOrden.PAGADA)  # revalida el cupón y lo consume si ganó
        consumido = cupon_reg is not None and cupon_reg.cupon.usos_actuales > usos_antes
        uow.pagos.agregar(PagoRegistro(
            None, orden_id, "simulado", f"sim_{secrets.token_hex(8)}", orden.total, "PAGADO",
        ))
        _cerrar_como_pagada(uow, registro, cuenta, cupon_reg, consumido, rfc)
        respuesta = orden_a_json(uow, registro, actual.id)
        uow.commit()
        return respuesta


# ---- Pago con pasarela (ADR 004) ----
def _sesion_a_json(pasarela: PasarelaDePago, orden_id: int, pago: PagoRegistro | None, monto) -> dict:
    return {
        "pasarela": pasarela.nombre, "orden_id": orden_id,
        "url": pago.url if pago else None, "monto": a_texto(monto),
        "expira_en": pago.expira_en.isoformat() if pago and pago.expira_en else None,
    }


def _cerrar_sesion(pasarela: PasarelaDePago, pago: PagoRegistro) -> None:
    try:
        cerrada = pasarela.cancelar_sesion(pago.referencia) if pago.referencia else True
    except PasarelaNoDisponible as exc:
        raise ServicioNoDisponible(str(exc), "PASARELA_NO_DISPONIBLE") from exc
    if not cerrada:
        # Ya se cobró: el aviso de la pasarela está por llegar y marcará la orden como pagada.
        raise Conflicto("Tu pago ya se realizó; en un momento verás tu pedido confirmado", "PAGO_YA_REALIZADO")
    pago.estado = "EXPIRADO"


def iniciar_pago(fabrica: FabricaUoW, pasarela: PasarelaDePago, actual: UsuarioActual, orden_id: int,
                 url_frontend: str) -> dict:
    """Abre el cobro de la orden en la pasarela con el monto que calcula el servidor.

    Con el simulado solo devuelve el monto (el cliente sigue con POST /pagar). Con Stripe crea la
    sesión de Checkout y devuelve su URL; si ya hay una abierta y vigente, devuelve la misma para
    no abrir dos cobros de la misma orden.
    """
    with fabrica() as uow:
        registro = _orden_propia(uow, orden_id, actual, bloquear=True)
        if registro.orden.estado is not EstadoOrden.CREADA:
            raise Conflicto("Esta orden ya fue pagada", "ORDEN_YA_PAGADA")
        if not pasarela.redirige:
            _preparar_cobro(uow, registro, actual)
            return _sesion_a_json(pasarela, orden_id, None, registro.orden.total)

        ahora = _ahora()
        pendiente = uow.pagos.pendiente_de_orden(orden_id, bloquear=True)
        if pendiente is not None:
            if pendiente.url and pendiente.expira_en and pendiente.expira_en > ahora + timedelta(minutes=2):
                return _sesion_a_json(pasarela, orden_id, pendiente, pendiente.monto)
            _cerrar_sesion(pasarela, pendiente)  # vencida o a punto de vencer: se abre otra
            uow.pagos.guardar(pendiente)

        _preparar_cobro(uow, registro, actual)
        uow.ordenes.guardar(registro)  # el monto que se cobra es el que queda guardado
        monto = registro.orden.total
        expira = ahora + VIGENCIA_PAGO + timedelta(minutes=1)
        pago = uow.pagos.agregar(PagoRegistro(None, orden_id, pasarela.nombre, None, monto, expira_en=expira))
        punto = uow.puntos_venta.por_id(registro.punto_venta_id)
        cuenta = uow.usuarios.por_id(actual.id)
        try:
            sesion = pasarela.crear_sesion(
                pago_id=pago.id, orden_id=orden_id, monto=monto,
                descripcion=f"FACFOOD · Pedido #{orden_id} · {punto.nombre}", correo=cuenta.correo,
                url_exito=f"{url_frontend}/pedido/{orden_id}/pago?resultado=exito",
                url_cancelar=f"{url_frontend}/pedido/{orden_id}/pago?resultado=cancelado",
                expira_en=expira,
            )
        except PasarelaNoDisponible as exc:
            raise ServicioNoDisponible(str(exc), "PASARELA_NO_DISPONIBLE") from exc
        pago.referencia, pago.url = sesion.referencia, sesion.url
        uow.pagos.guardar(pago)
        uow.commit()
        return _sesion_a_json(pasarela, orden_id, pago, monto)


def cancelar_pago(fabrica: FabricaUoW, pasarela: PasarelaDePago, actual: UsuarioActual, orden_id: int) -> dict:
    """Cierra el cobro abierto para que el comprador pueda volver a editar su pedido."""
    with fabrica() as uow:
        registro = _orden_propia(uow, orden_id, actual, bloquear=True)
        pendiente = uow.pagos.pendiente_de_orden(orden_id, bloquear=True)
        if pendiente is not None:
            _cerrar_sesion(pasarela, pendiente)
            uow.pagos.guardar(pendiente)
        respuesta = orden_a_json(uow, registro, actual.id)
        uow.commit()
        return respuesta


def procesar_evento(fabrica: FabricaUoW, pasarela: PasarelaDePago, evento: EventoDePago) -> str:
    """Aplica un aviso ya verificado de la pasarela. Es idempotente: la pasarela reintenta los
    avisos y el mismo puede llegar varias veces. Devuelve qué se hizo (para la bitácora)."""
    if evento.tipo == "ignorado" or not evento.referencia:
        return "ignorado"
    with fabrica() as uow:
        pago = uow.pagos.por_referencia(pasarela.nombre, evento.referencia)
        if pago is None:
            log.error("Aviso %s de una sesión desconocida %s", evento.id, evento.referencia)
            return "desconocido"
        # Mismo orden de candados que iniciar_pago (orden y luego pago) para no trabarse entre sí.
        registro = uow.ordenes.por_id(pago.orden_id, bloquear=True)
        pago = uow.pagos.por_referencia(pasarela.nombre, evento.referencia, bloquear=True)

        if evento.tipo in ("expirado", "fallido"):
            if pago.estado != "PENDIENTE":
                return "repetido"
            pago.estado, pago.evento_id = ("EXPIRADO" if evento.tipo == "expirado" else "FALLIDO"), evento.id
            uow.pagos.guardar(pago)
            uow.commit()
            return pago.estado.lower()

        # evento.tipo == "pagado"
        if pago.estado == "PAGADO":
            return "repetido"
        if evento.orden_id != pago.orden_id or evento.moneda != "mxn" or evento.monto != pago.monto:
            log.error("Aviso %s no coincide con el pago %s (orden, moneda o monto)", evento.id, pago.id)
            return "no_coincide"

        pago.estado, pago.evento_id = "PAGADO", evento.id
        uow.pagos.guardar(pago)
        orden = registro.orden
        if orden.estado is EstadoOrden.CREADA and orden.total == pago.monto:
            cuenta = uow.usuarios.por_id(registro.comprador_id)
            cupon_reg = uow.cupones.por_id(registro.cupon_id, bloquear=True) if registro.cupon_id else None
            consumido = orden.confirmar_cobro(cupon_reg.cupon if cupon_reg else None)
            _cerrar_como_pagada(uow, registro, cuenta, cupon_reg, consumido, None)
        else:
            # No debería pasar (la orden no se puede editar con un pago en curso): se cobró, pero
            # la orden cambió. Queda registrado para revisarlo y reembolsar a mano.
            log.error("Pago %s cobrado pero la orden %s está %s con total %s", pago.id, registro.id,
                      orden.estado.value, orden.total)
        uow.commit()
        return "pagado"
