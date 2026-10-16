# Contrato entre las dos mitades de FACFOOD

Sebastián implementa las vistas **01–04** y Arturo las **05–08**, cada uno con su backend.
Este documento es lo **único** que comparten. Si algo de aquí tiene que cambiar, se acuerda
entre los dos **antes** de integrar el PR.

## 1. Quién es dueño de qué

| | Sebastián (01–04) | Arturo (05–08) |
|---|---|---|
| Backend | `app/cuentas/`, `app/catalogo/`, `app/checkout/` | `app/seguimiento/`, `app/vendedor/`, `app/entregas/` |
| Frontend | `features/cuenta|explorar|menu|carrito/`, `app/rutas-sebastian.tsx`, `app/proveedores.tsx` | `features/seguimiento|vendedor|repartidor/`, `app/rutas-arturo.tsx` |
| Compartido (no se toca sin acordar) | `app/shared/`, `app/ports/`, `app/adapters/`, `app/domain/`, `migrations/`, `app/seed.py`, `src/components/`, `src/api/`, este archivo | ← |

`app/domain/` es compartido: si alguno necesita cambiar una regla de negocio, abre un PR
solo con ese cambio y su prueba, y el otro lo revisa.

## 2. Tablas: quién escribe

Todas existen desde la migración `0001_esquema_base`.

| Tabla | Escribe | Lee |
|---|---|---|
| `usuarios` | Sebastián (registro, perfil dual). Arturo solo suma `pedidos_completados` al entregar | ambos |
| `puntos_venta`, `productos`, `destinos` | Sebastián (y datos de ejemplo). Arturo solo cambia `puntos_venta.abierto` | ambos |
| `cupones`, `usos_cupon` | Sebastián | — |
| `ordenes`, `lineas_orden` | Sebastián: **CREADA → PAGADA**. Arturo: **PAGADA → … → ENTREGADA** | ambos |
| `orden_eventos` | cada quien registra las transiciones de su tramo | Arturo (línea de tiempo) |
| `facturas` | Sebastián (se genera **al pagar**) | Arturo (descarga) |
| `entregas` | Arturo | — |

## 3. Estados de la orden

```
CREADA ──pagar──▶ PAGADA ──▶ EN_PREPARACION ──▶ ENVIADA ──▶ ENTREGADA
   └──────▶ CANCELADA
```

- Las transiciones siempre se hacen con `Orden.avanzar_estado()` del dominio (valida la secuencia).
- Cada transición agrega una fila a `orden_eventos` con `estado`, `actor_id` y `creado_en`.
- Para **pickup**, ENVIADA significa "listo para recoger". Para **entrega estudiante**,
  ENVIADA significa "el repartidor ya lo recogió y va en camino".
- Al pasar a ENTREGADA, quien entrega suma 1 a `usuarios.pedidos_completados` del comprador
  (`Usuario.registrar_pedido_completado()`); eso alimenta la lealtad y el perfil dual.

## 4. Entrega por estudiante

- Costo de envío = `distancia_km × $5` (`EntregaEstudiante.COSTO_POR_KM`). Lo calcula el
  checkout al crear la orden; la distancia es puesto → destino con PostGIS.
- La ganancia del repartidor es el `envio` de la orden.
- `ordenes.codigo_entrega` (4 dígitos) lo genera el checkout **al pagar** y solo para entrega
  estudiante. El comprador lo ve en la vista 05; el repartidor lo pide al entregar (vista 08).
- Una orden es "entrega disponible" (vista 07) si `metodo_entrega = 'estudiante'`,
  su estado es `PAGADA` o `EN_PREPARACION` y no tiene fila en `entregas`.

## 5. Autenticación

Todos los endpoints protegidos usan `Depends(get_usuario_actual)` → `UsuarioActual(id, rol)`.
Roles: `comprador`, `vendedor`, `repartidor`. Para exigir un rol: `Depends(exigir_rol("vendedor"))`.

En desarrollo se puede entrar como un usuario de ejemplo con el encabezado `X-Usuario-Id`
(en el frontend: botón **DEV** arriba a la derecha). Usuarios de ejemplo (contraseña `facfood123`):

| id | correo | rol |
|---|---|---|
| 1 | diana@facfood.mx | comprador (0 pedidos) |
| 2 | sebastian@facfood.mx | comprador (3 pedidos) |
| 3 | memo@facfood.mx | vendedor de Tacos Don Memo |
| 4 | lupita@facfood.mx | vendedor de Chilaquiles Lupita |
| 5 | arturo@facfood.mx | repartidor |

Órdenes de ejemplo para las vistas 05–08: #1 (PAGADA, entrega), #2 (EN_PREPARACION, pickup),
#3 (PAGADA, entrega), #4 (ENTREGADA, pickup). Todas tienen factura y eventos.

## 6. Objeto Orden (JSON)

Lo devuelven los endpoints de checkout y lo usa la vista 05. **El dinero siempre es texto con
2 decimales**; el frontend nunca calcula montos de una orden.

```json
{
  "id": 7,
  "estado": "PAGADA",
  "comprador_id": 1,
  "punto_venta": { "id": 1, "nombre": "Tacos Don Memo" },
  "lineas": [
    { "producto_id": 1, "nombre": "Taco de pastor", "cantidad": 2,
      "precio_unitario": "18.00", "importe": "36.00" }
  ],
  "metodo_entrega": "estudiante",
  "destino": { "id": 2, "nombre": "Facultad de Arquitectura" },
  "distancia_km": "0.60",
  "subtotal": "66.00",
  "descuento": "9.90",
  "origen_descuento": "cupon",
  "cupon": "BIENVENIDA15",
  "iva": "8.98",
  "envio": "3.00",
  "total": "68.08",
  "codigo_entrega": "4821",
  "factura_folio": "8f0c…",
  "creada_en": "2026-10-16T19:02:00Z"
}
```

- `origen_descuento`: `"cupon"`, `"lealtad"` o `null`. Los descuentos no se acumulan: se aplica el mayor.
- `destino`, `codigo_entrega` y `factura_folio` pueden ser `null`.
- `codigo_entrega` solo se incluye para el comprador de la orden y para quien la entrega.

## 7. Errores

Toda respuesta de error: `{"detail": "mensaje para el usuario", "codigo": "CUPON_INVALIDO"}`.
401 sin sesión · 403 sin el rol · 404 no existe · 409 transición o estado inválido · 422 datos o regla de negocio.

## 8. Endpoints

| Vista | Método y ruta | Dueño |
|---|---|---|
| 01 | `POST /auth/registro`, `POST /auth/login`, `GET /usuarios/me`, `POST /usuarios/me/vendedor` | Sebastián |
| 02 | `GET /puntos-venta?lat=&lon=&radio=&categoria=&q=`, `GET /puntos-venta/categorias` | Sebastián |
| 03 | `GET /puntos-venta/{id}`, `GET /puntos-venta/{id}/productos` | Sebastián |
| 04 | `GET /destinos`, `POST /ordenes`, `PATCH /ordenes/{id}/entrega`, `POST`/`DELETE /ordenes/{id}/cupon`, `POST /ordenes/{id}/pagar` | Sebastián |
| 05 | `GET /ordenes/{id}` (orden + `eventos`), `GET /ordenes/{id}/factura` | Arturo |
| 06 | `GET /vendedor/ordenes`, `POST /ordenes/{id}/estado`, `PATCH /puntos-venta/{id}` (abierto) | Arturo |
| 07–08 | `GET /entregas/disponibles`, `POST /entregas/{orden_id}/aceptar`, `/recoger`, `/entregar` | Arturo |

Al pagar, la vista 04 navega a `/pedido/{id}` (vista 05): es el único punto donde se tocan
los frontends de los dos.
