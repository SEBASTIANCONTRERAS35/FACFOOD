"""Adaptador en memoria: implementa los puertos sin base de datos.

Sirve para las pruebas y para levantar la app sin Docker. Imita una
transacción: cada unidad de trabajo toma un candado global (como un
SELECT ... FOR UPDATE, pero de todo el almacén) y, si no se hace commit()
o hay una excepción, restaura la copia tomada al entrar.
"""

import copy
import threading
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone

from app.ports.repositorios import PuntoVentaCercano
from app.shared.geo import distancia_m


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class _Datos:
    usuarios: dict = field(default_factory=dict)
    puntos_venta: dict = field(default_factory=dict)
    productos: dict = field(default_factory=dict)
    destinos: dict = field(default_factory=dict)
    cupones: dict = field(default_factory=dict)
    usos_cupon: list = field(default_factory=list)  # (cupon_id, usuario_id, orden_id)
    ordenes: dict = field(default_factory=dict)
    eventos: list = field(default_factory=list)
    facturas: dict = field(default_factory=dict)
    secuencias: dict = field(default_factory=dict)

    def siguiente_id(self, tabla: str) -> int:
        self.secuencias[tabla] = self.secuencias.get(tabla, 0) + 1
        return self.secuencias[tabla]


class AlmacenMemoria:
    def __init__(self):
        self.datos = _Datos()
        self.candado = threading.RLock()


class _Repo:
    def __init__(self, datos: _Datos):
        self.d = datos


class UsuarioRepoMemoria(_Repo):
    def agregar(self, cuenta):
        cuenta = copy.deepcopy(cuenta)
        cuenta.id = self.d.siguiente_id("usuarios")
        cuenta.creado_en = cuenta.creado_en or _ahora()
        self.d.usuarios[cuenta.id] = cuenta
        return copy.deepcopy(cuenta)

    def guardar(self, cuenta):
        self.d.usuarios[cuenta.id] = copy.deepcopy(cuenta)

    def por_id(self, usuario_id):
        return copy.deepcopy(self.d.usuarios.get(usuario_id))

    def por_correo(self, correo):
        correo = correo.strip().lower()
        for c in self.d.usuarios.values():
            if c.correo == correo:
                return copy.deepcopy(c)
        return None

    def existe_credencial(self, credencial_unam):
        return any(c.usuario.credencial_unam == credencial_unam for c in self.d.usuarios.values())

    def listar(self):
        return [copy.deepcopy(c) for c in sorted(self.d.usuarios.values(), key=lambda c: c.id)]


class PuntoVentaRepoMemoria(_Repo):
    def agregar(self, punto):
        punto = replace(punto, id=self.d.siguiente_id("puntos_venta"))
        self.d.puntos_venta[punto.id] = punto
        return punto

    def por_id(self, punto_id):
        return self.d.puntos_venta.get(punto_id)

    def cercanos(self, lat, lon, radio_m, categoria=None, texto=None):
        texto = (texto or "").strip().lower()
        resultado = []
        for p in self.d.puntos_venta.values():
            if categoria and p.categoria.lower() != categoria.lower():
                continue
            if texto and texto not in p.nombre.lower() and texto not in p.categoria.lower():
                continue
            dist = distancia_m(lat, lon, p.lat, p.lon)
            if dist <= radio_m:
                resultado.append(PuntoVentaCercano(p, round(dist)))
        return sorted(resultado, key=lambda c: (c.distancia_m, c.punto.id))

    def distancia_m(self, punto_id, lat, lon):
        p = self.d.puntos_venta[punto_id]
        return round(distancia_m(lat, lon, p.lat, p.lon))

    def categorias(self):
        return sorted({p.categoria for p in self.d.puntos_venta.values()})

    def cambiar_abierto(self, punto_id, abierto):
        self.d.puntos_venta[punto_id] = replace(self.d.puntos_venta[punto_id], abierto=abierto)


class ProductoRepoMemoria(_Repo):
    def agregar(self, producto):
        producto = replace(producto, id=self.d.siguiente_id("productos"))
        self.d.productos[producto.id] = producto
        return producto

    def de_punto(self, punto_id):
        return sorted(
            (p for p in self.d.productos.values() if p.punto_venta_id == punto_id),
            key=lambda p: p.id,
        )


class DestinoRepoMemoria(_Repo):
    def agregar(self, destino):
        destino = replace(destino, id=self.d.siguiente_id("destinos"))
        self.d.destinos[destino.id] = destino
        return destino

    def listar(self):
        return sorted(self.d.destinos.values(), key=lambda x: x.nombre)

    def por_id(self, destino_id):
        return self.d.destinos.get(destino_id)


class CuponRepoMemoria(_Repo):
    def agregar(self, registro):
        registro = copy.deepcopy(registro)
        registro.id = self.d.siguiente_id("cupones")
        self.d.cupones[registro.id] = registro
        return copy.deepcopy(registro)

    def guardar(self, registro):
        self.d.cupones[registro.id] = copy.deepcopy(registro)

    def por_id(self, cupon_id, bloquear=False):
        # El candado global de la unidad de trabajo ya serializa el acceso.
        return copy.deepcopy(self.d.cupones.get(cupon_id))

    def por_codigo(self, codigo):
        codigo = codigo.strip().upper()
        for r in self.d.cupones.values():
            if r.cupon.codigo.upper() == codigo:
                return copy.deepcopy(r)
        return None

    def usos_de_usuario(self, cupon_id, usuario_id):
        return sum(1 for c, u, _ in self.d.usos_cupon if c == cupon_id and u == usuario_id)

    def registrar_uso(self, cupon_id, usuario_id, orden_id):
        self.d.usos_cupon.append((cupon_id, usuario_id, orden_id))


class OrdenRepoMemoria(_Repo):
    def agregar(self, registro):
        registro = copy.deepcopy(registro)
        registro.id = self.d.siguiente_id("ordenes")
        registro.creada_en = registro.creada_en or _ahora()
        self.d.ordenes[registro.id] = registro
        return copy.deepcopy(registro)

    def guardar(self, registro):
        self.d.ordenes[registro.id] = copy.deepcopy(registro)

    def por_id(self, orden_id, bloquear=False):
        return copy.deepcopy(self.d.ordenes.get(orden_id))

    def de_punto(self, punto_id):
        return [
            copy.deepcopy(r)
            for r in sorted(self.d.ordenes.values(), key=lambda r: r.id)
            if r.punto_venta_id == punto_id
        ]


class EventoRepoMemoria(_Repo):
    def agregar(self, evento):
        self.d.eventos.append(evento)

    def de_orden(self, orden_id):
        return sorted((e for e in self.d.eventos if e.orden_id == orden_id), key=lambda e: e.creado_en)


class FacturaRepoMemoria(_Repo):
    def agregar(self, registro):
        self.d.facturas[registro.orden_id] = registro

    def de_orden(self, orden_id):
        return self.d.facturas.get(orden_id)


class UnidadDeTrabajoMemoria:
    def __init__(self, almacen: AlmacenMemoria):
        self._almacen = almacen

    def __enter__(self):
        self._almacen.candado.acquire()
        self._respaldo = copy.deepcopy(self._almacen.datos)
        self._confirmado = False
        d = self._almacen.datos
        self.usuarios = UsuarioRepoMemoria(d)
        self.puntos_venta = PuntoVentaRepoMemoria(d)
        self.productos = ProductoRepoMemoria(d)
        self.destinos = DestinoRepoMemoria(d)
        self.cupones = CuponRepoMemoria(d)
        self.ordenes = OrdenRepoMemoria(d)
        self.eventos = EventoRepoMemoria(d)
        self.facturas = FacturaRepoMemoria(d)
        return self

    def __exit__(self, tipo, valor, traza):
        try:
            if tipo is not None or not self._confirmado:
                self._almacen.datos = self._respaldo
        finally:
            self._almacen.candado.release()

    def commit(self):
        self._confirmado = True
