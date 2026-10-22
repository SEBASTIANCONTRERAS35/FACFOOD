"""Adaptador PostgreSQL + PostGIS de los puertos de persistencia."""

from decimal import Decimal

from geoalchemy2 import Geometry, WKTElement
from sqlalchemy import cast, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.adapters.postgres.modelos import (
    CuponM,
    DestinoM,
    EventoOrdenM,
    FacturaM,
    LineaOrdenM,
    OrdenM,
    ProductoM,
    PuntoVentaM,
    UsoCuponM,
    UsuarioM,
)
from app.domain.crm.retencion import Cupon
from app.domain.erp.factura import Factura
from app.domain.erp.orden import LineaPedido, Orden
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
    PuntoVentaCercano,
)
from app.shared.errores import Conflicto


def _punto_wkt(lat: float, lon: float) -> WKTElement:
    return WKTElement(f"POINT({float(lon)} {float(lat)})", srid=4326)


def _geog(lat: float, lon: float):
    return func.ST_GeogFromText(f"SRID=4326;POINT({float(lon)} {float(lat)})")


class _Repo:
    def __init__(self, sesion: Session):
        self.s = sesion


# ---- Usuarios ----
def _a_cuenta(m: UsuarioM) -> CuentaUsuario:
    usuario = Usuario.restaurar(
        m.nombre, m.credencial_unam, m.password_hash, m.rol, m.pedidos_completados
    )
    return CuentaUsuario(m.id, m.correo, usuario, m.creado_en)


class UsuarioRepoPg(_Repo):
    def agregar(self, cuenta):
        u = cuenta.usuario
        m = UsuarioM(
            correo=cuenta.correo.strip().lower(), nombre=u.nombre, credencial_unam=u.credencial_unam,
            password_hash=u.password_hash, consentimiento_datos=u.consentimiento_datos,
            rol=u.rol, pedidos_completados=u.pedidos_completados,
        )
        self.s.add(m)
        try:
            self.s.flush()
        except IntegrityError:
            # Dos registros simultáneos con el mismo correo o credencial.
            raise Conflicto("Ya existe una cuenta con ese correo o número de cuenta", "CUENTA_DUPLICADA")
        return _a_cuenta(m)

    def guardar(self, cuenta):
        m = self.s.get(UsuarioM, cuenta.id)
        u = cuenta.usuario
        m.nombre, m.rol, m.pedidos_completados = u.nombre, u.rol, u.pedidos_completados
        m.password_hash = u.password_hash
        self.s.flush()

    def por_id(self, usuario_id):
        m = self.s.get(UsuarioM, usuario_id)
        return _a_cuenta(m) if m else None

    def por_correo(self, correo):
        m = self.s.scalar(select(UsuarioM).where(UsuarioM.correo == correo.strip().lower()))
        return _a_cuenta(m) if m else None

    def existe_credencial(self, credencial_unam):
        return self.s.scalar(
            select(func.count()).select_from(UsuarioM).where(UsuarioM.credencial_unam == credencial_unam)
        ) > 0

    def listar(self):
        return [_a_cuenta(m) for m in self.s.scalars(select(UsuarioM).order_by(UsuarioM.id))]


# ---- Puntos de venta ----
_LAT = func.ST_Y(cast(PuntoVentaM.ubicacion, Geometry)).label("lat")
_LON = func.ST_X(cast(PuntoVentaM.ubicacion, Geometry)).label("lon")


def _a_punto(m: PuntoVentaM, lat: float, lon: float) -> PuntoVenta:
    return PuntoVenta(
        id=m.id, vendedor_id=m.vendedor_id, nombre=m.nombre, categoria=m.categoria,
        descripcion=m.descripcion, ubicacion_texto=m.ubicacion_texto, lat=float(lat), lon=float(lon),
        calificacion=Decimal(m.calificacion), num_resenas=m.num_resenas,
        horario_cierre=m.horario_cierre, abierto=m.abierto, admite_entrega=m.admite_entrega,
    )


class PuntoVentaRepoPg(_Repo):
    def agregar(self, punto):
        m = PuntoVentaM(
            vendedor_id=punto.vendedor_id, nombre=punto.nombre, categoria=punto.categoria,
            descripcion=punto.descripcion, ubicacion_texto=punto.ubicacion_texto,
            ubicacion=_punto_wkt(punto.lat, punto.lon), calificacion=punto.calificacion,
            num_resenas=punto.num_resenas, horario_cierre=punto.horario_cierre,
            abierto=punto.abierto, admite_entrega=punto.admite_entrega,
        )
        self.s.add(m)
        self.s.flush()
        return self.por_id(m.id)

    def por_id(self, punto_id):
        fila = self.s.execute(select(PuntoVentaM, _LAT, _LON).where(PuntoVentaM.id == punto_id)).first()
        return _a_punto(*fila) if fila else None

    def cercanos(self, lat, lon, radio_m, categoria=None, texto=None):
        origen = _geog(lat, lon)
        distancia = func.ST_Distance(PuntoVentaM.ubicacion, origen).label("distancia")
        consulta = (
            select(PuntoVentaM, _LAT, _LON, distancia)
            .where(func.ST_DWithin(PuntoVentaM.ubicacion, origen, radio_m))
            .order_by(distancia, PuntoVentaM.id)
        )
        if categoria:
            consulta = consulta.where(func.lower(PuntoVentaM.categoria) == categoria.lower())
        if texto and texto.strip():
            patron = f"%{texto.strip()}%"
            consulta = consulta.where(
                or_(PuntoVentaM.nombre.ilike(patron), PuntoVentaM.categoria.ilike(patron))
            )
        return [
            PuntoVentaCercano(_a_punto(m, la, lo), round(d))
            for m, la, lo, d in self.s.execute(consulta)
        ]

    def distancia_m(self, punto_id, lat, lon):
        d = self.s.scalar(
            select(func.ST_Distance(PuntoVentaM.ubicacion, _geog(lat, lon))).where(PuntoVentaM.id == punto_id)
        )
        return round(d)

    def categorias(self):
        return list(self.s.scalars(select(PuntoVentaM.categoria).distinct().order_by(PuntoVentaM.categoria)))

    def de_vendedor(self, vendedor_id):
        filas = self.s.execute(select(PuntoVentaM, _LAT, _LON).where(PuntoVentaM.vendedor_id == vendedor_id).order_by(PuntoVentaM.id)).all()
        return [_a_punto(*fila) for fila in filas]

    def cambiar_abierto(self, punto_id, abierto):
        self.s.get(PuntoVentaM, punto_id).abierto = abierto
        self.s.flush()


# ---- Productos y destinos ----
def _a_producto(m: ProductoM) -> Producto:
    return Producto(m.id, m.punto_venta_id, m.nombre, m.descripcion, Decimal(m.precio), m.disponible)


class ProductoRepoPg(_Repo):
    def agregar(self, producto):
        m = ProductoM(
            punto_venta_id=producto.punto_venta_id, nombre=producto.nombre,
            descripcion=producto.descripcion, precio=producto.precio, disponible=producto.disponible,
        )
        self.s.add(m)
        self.s.flush()
        return _a_producto(m)

    def de_punto(self, punto_id):
        return [
            _a_producto(m)
            for m in self.s.scalars(
                select(ProductoM).where(ProductoM.punto_venta_id == punto_id).order_by(ProductoM.id)
            )
        ]


_DLAT = func.ST_Y(cast(DestinoM.ubicacion, Geometry))
_DLON = func.ST_X(cast(DestinoM.ubicacion, Geometry))


class DestinoRepoPg(_Repo):
    def agregar(self, destino):
        m = DestinoM(nombre=destino.nombre, ubicacion=_punto_wkt(destino.lat, destino.lon))
        self.s.add(m)
        self.s.flush()
        return Destino(m.id, destino.nombre, destino.lat, destino.lon)

    def listar(self):
        filas = self.s.execute(select(DestinoM.id, DestinoM.nombre, _DLAT, _DLON).order_by(DestinoM.nombre))
        return [Destino(i, n, float(la), float(lo)) for i, n, la, lo in filas]

    def por_id(self, destino_id):
        fila = self.s.execute(
            select(DestinoM.id, DestinoM.nombre, _DLAT, _DLON).where(DestinoM.id == destino_id)
        ).first()
        return Destino(fila[0], fila[1], float(fila[2]), float(fila[3])) if fila else None


# ---- Cupones ----
def _a_cupon(m: CuponM) -> CuponRegistro:
    cupon = Cupon(
        codigo=m.codigo, porcentaje=float(m.porcentaje), vigente_hasta=m.vigente_hasta,
        pedido_minimo=float(m.pedido_minimo),
        tope_descuento=float(m.tope_descuento) if m.tope_descuento is not None else None,
        usos_maximos=m.usos_maximos,
    )
    cupon.usos_actuales = m.usos_actuales
    return CuponRegistro(m.id, cupon, m.solo_primer_pedido, m.uno_por_usuario)


class CuponRepoPg(_Repo):
    def agregar(self, registro):
        c = registro.cupon
        m = CuponM(
            codigo=c.codigo.upper(), porcentaje=Decimal(str(c.porcentaje)), vigente_hasta=c.vigente_hasta,
            pedido_minimo=Decimal(str(c.pedido_minimo)),
            tope_descuento=Decimal(str(c.tope_descuento)) if c.tope_descuento is not None else None,
            usos_maximos=c.usos_maximos, usos_actuales=c.usos_actuales,
            solo_primer_pedido=registro.solo_primer_pedido, uno_por_usuario=registro.uno_por_usuario,
        )
        self.s.add(m)
        self.s.flush()
        return _a_cupon(m)

    def guardar(self, registro):
        m = self.s.get(CuponM, registro.id)
        m.usos_actuales = registro.cupon.usos_actuales
        self.s.flush()

    def por_id(self, cupon_id, bloquear=False):
        consulta = select(CuponM).where(CuponM.id == cupon_id)
        if bloquear:
            # Dos pagos simultáneos con el mismo cupón se forman en fila aquí.
            consulta = consulta.with_for_update().execution_options(populate_existing=True)
        m = self.s.scalar(consulta)
        return _a_cupon(m) if m else None

    def por_codigo(self, codigo):
        m = self.s.scalar(select(CuponM).where(CuponM.codigo == codigo.strip().upper()))
        return _a_cupon(m) if m else None

    def usos_de_usuario(self, cupon_id, usuario_id):
        return self.s.scalar(
            select(func.count()).select_from(UsoCuponM)
            .where(UsoCuponM.cupon_id == cupon_id, UsoCuponM.usuario_id == usuario_id)
        )

    def registrar_uso(self, cupon_id, usuario_id, orden_id):
        self.s.add(UsoCuponM(cupon_id=cupon_id, usuario_id=usuario_id, orden_id=orden_id))
        self.s.flush()


# ---- Órdenes ----
class OrdenRepoPg(_Repo):
    def _a_registro(self, m: OrdenM) -> OrdenRegistro:
        catalogo = {
            str(p.id): Decimal(p.precio)
            for p in self.s.scalars(select(ProductoM).where(ProductoM.punto_venta_id == m.punto_venta_id))
        }
        lineas = [
            LineaPedido(str(l.producto_id), l.cantidad, Decimal(l.precio_unitario))
            for l in self.s.scalars(
                select(LineaOrdenM).where(LineaOrdenM.orden_id == m.id).order_by(LineaOrdenM.id)
            )
        ]
        cupon = None
        if m.cupon_id is not None:
            cupon = _a_cupon(self.s.get(CuponM, m.cupon_id)).cupon
        orden = Orden.restaurar(
            catalogo, m.fecha, m.estado, lineas, Decimal(m.descuento), Decimal(m.envio), cupon,
            pedidos_completados=m.pedidos_completados_al_crear,
            origen_descuento=m.origen_descuento,
        )
        return OrdenRegistro(
            id=m.id, comprador_id=m.comprador_id, punto_venta_id=m.punto_venta_id, orden=orden,
            metodo_entrega=m.metodo_entrega, destino_id=m.destino_id,
            distancia_km=Decimal(m.distancia_km), cupon_id=m.cupon_id,
            pedidos_completados_al_crear=m.pedidos_completados_al_crear,
            codigo_entrega=m.codigo_entrega, creada_en=m.creada_en,
        )

    def _copiar(self, m: OrdenM, r: OrdenRegistro) -> None:
        o = r.orden
        m.estado = o.estado.value
        m.fecha = o.fecha
        m.metodo_entrega = r.metodo_entrega
        m.destino_id = r.destino_id
        m.distancia_km = r.distancia_km
        m.cupon_id = r.cupon_id
        m.pedidos_completados_al_crear = r.pedidos_completados_al_crear
        m.subtotal, m.descuento, m.iva, m.envio, m.total = o.subtotal, o.descuentos, o.iva, o.envio, o.total
        m.origen_descuento = o.origen_descuento
        m.codigo_entrega = r.codigo_entrega

    def _guardar_lineas(self, m: OrdenM, r: OrdenRegistro) -> None:
        for l in list(self.s.scalars(select(LineaOrdenM).where(LineaOrdenM.orden_id == m.id))):
            self.s.delete(l)
        for l in r.orden.lineas:
            self.s.add(LineaOrdenM(
                orden_id=m.id, producto_id=int(l.producto_id), cantidad=l.cantidad,
                precio_unitario=l.precio_unitario,
            ))

    def agregar(self, registro):
        m = OrdenM(comprador_id=registro.comprador_id, punto_venta_id=registro.punto_venta_id)
        if registro.creada_en is not None:
            m.creada_en = registro.creada_en
        self._copiar(m, registro)
        self.s.add(m)
        self.s.flush()
        self._guardar_lineas(m, registro)
        self.s.flush()
        return self._a_registro(m)

    def guardar(self, registro):
        m = self.s.get(OrdenM, registro.id)
        self._copiar(m, registro)
        self._guardar_lineas(m, registro)
        self.s.flush()

    def por_id(self, orden_id, bloquear=False):
        consulta = select(OrdenM).where(OrdenM.id == orden_id)
        if bloquear:
            consulta = consulta.with_for_update().execution_options(populate_existing=True)
        m = self.s.scalar(consulta)
        return self._a_registro(m) if m else None

    def de_punto(self, punto_id):
        return [
            self._a_registro(m)
            for m in self.s.scalars(select(OrdenM).where(OrdenM.punto_venta_id == punto_id).order_by(OrdenM.id))
        ]


# ---- Eventos y facturas ----
class EventoRepoPg(_Repo):
    def agregar(self, evento):
        self.s.add(EventoOrdenM(
            orden_id=evento.orden_id, estado=evento.estado, actor_id=evento.actor_id, creado_en=evento.creado_en,
        ))
        self.s.flush()

    def de_orden(self, orden_id):
        return [
            EventoOrden(m.orden_id, m.estado, m.creado_en, m.actor_id)
            for m in self.s.scalars(
                select(EventoOrdenM).where(EventoOrdenM.orden_id == orden_id)
                .order_by(EventoOrdenM.creado_en, EventoOrdenM.id)
            )
        ]


class FacturaRepoPg(_Repo):
    def agregar(self, registro):
        f = registro.factura
        self.s.add(FacturaM(
            folio_fiscal=f.folio_fiscal, orden_id=registro.orden_id, rfc_receptor=f.rfc_receptor,
            xml=f.xml_data.decode("utf-8"), creada_en=registro.creada_en,
        ))
        self.s.flush()

    def de_orden(self, orden_id):
        m = self.s.scalar(select(FacturaM).where(FacturaM.orden_id == orden_id))
        if m is None:
            return None
        return FacturaRegistro(
            m.orden_id, Factura(m.folio_fiscal, m.rfc_receptor, m.xml.encode("utf-8")), m.creada_en
        )
