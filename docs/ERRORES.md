# Catálogo de errores de la API (RFC 7807)

Cada error responde `application/problem+json` con esta forma:

```json
{
  "type": "https://github.com/SEBASTIANCONTRERAS35/FACFOOD/blob/main/docs/ERRORES.md#validacion",
  "title": "Error de validación en los datos de entrada",
  "status": 400,
  "detail": "Uno o más campos del payload no cumplen con las reglas establecidas.",
  "instance": "/auth/registro",
  "codigo": "VALIDACION",
  "invalid_params": [{ "name": "credencial_unam", "reason": "El número de cuenta UNAM tiene 9 dígitos" }]
}
```

- `type` apunta a la sección de este documento; `title` es fijo por tipo; `detail` explica esta ocurrencia.
- `codigo` es una extensión estable para que el frontend reaccione; `invalid_params` solo aparece en el 400.
- **Ningún error repite lo que envió el usuario** (contraseñas, códigos de entrega).
- Criterio de status: **400** DTO inválido · **401** sin sesión · **403** sin rol · **404** no existe · **409** conflicto de estado · **422** regla de negocio.

Implementación: `backend/app/shared/errores.py` (manejadores globales de FastAPI).

### `VALIDACION`

**400** · Error de validación en los datos de entrada — El JSON o los parámetros no cumplen el esquema del DTO. Trae `invalid_params` con cada campo y su motivo.

### `CREDENCIALES_INVALIDAS`

**401** · Credenciales inválidas — Correo o contraseña incorrectos (no revela cuál).

### `NO_AUTENTICADO`

**401** · Se requiere iniciar sesión — Falta el token o venció. Inicia sesión.

### `PROHIBIDO`

**403** · No tienes permiso para esta acción — Tu rol no permite la acción (ej. un comprador en el panel del vendedor).

### `CUPON_INEXISTENTE`

**404** · Cupón no encontrado — Ese código de cupón no existe.

### `NO_ENCONTRADO`

**404** · Recurso no encontrado — El recurso no existe o no es tuyo (no se revelan órdenes ajenas).

### `RUTA_NO_ENCONTRADA`

**404** · Ruta no encontrada — La ruta no existe en la API.

### `METODO_NO_PERMITIDO`

**405** · Método HTTP no permitido — La ruta existe pero no acepta ese método HTTP.

### `CONFLICTO`

**409** · Conflicto con el estado actual — Conflicto genérico con el estado actual.

### `CORREO_REGISTRADO`

**409** · Correo ya registrado — Ya hay una cuenta con ese correo.

### `CREDENCIAL_REGISTRADA`

**409** · Número de cuenta ya registrado — Ese número de cuenta UNAM ya está registrado.

### `CUENTA_DUPLICADA`

**409** · Cuenta duplicada — Dos registros simultáneos con el mismo correo o credencial.

### `ENTREGA_NO_DISPONIBLE`

**409** · Entrega no disponible — La orden ya no está disponible para reparto.

### `ENTREGA_YA_ACEPTADA`

**409** · Entrega ya aceptada — Otro repartidor ya aceptó la entrega.

### `ESTADO_ENTREGA_INVALIDO`

**409** · Estado de entrega inválido — La entrega no está en el paso correcto.

### `FACTURA_NO_PERMITIDA`

**409** · Factura no permitida — La factura solo se genera una vez, al pagar.

### `ORDEN_INMUTABLE`

**409** · La orden ya no se puede modificar — La orden ya salió de CREADA y no se puede editar.

### `ORDEN_NO_PAGADA`

**409** · La orden no está pagada — La operación requiere una orden pagada.

### `ORDEN_PENDIENTE_PREPARACION`

**409** · Orden pendiente de preparación — El repartidor quiso recoger antes de que el vendedor la preparara.

### `ORDEN_YA_PAGADA`

**409** · Orden ya pagada — Se intentó pagar una orden que ya no está CREADA.

### `PUESTO_CERRADO`

**409** · Puesto cerrado — El puesto está cerrado; no recibe órdenes.

### `ROL_INCOMPATIBLE`

**409** · Rol incompatible — Solo un comprador puede volverse vendedor.

### `TRANSICION_INVALIDA`

**409** · Transición de estado inválida — Salto de estado no permitido por la máquina de estados.

### `TRANSICION_NO_AUTORIZADA`

**409** · Transición de estado no autorizada — El vendedor intentó marcar enviada/entregada una entrega estudiante (lo hace el repartidor).

### `CODIGO_ENTREGA_INVALIDO`

**422** · Código de entrega inválido — El código de 4 dígitos no coincide.

### `CONSENTIMIENTO_REQUERIDO`

**422** · Se requiere consentimiento (LFPDPPP) — Registro sin consentimiento de datos (Art. 7 LFPDPPP).

### `CUPON_INVALIDO`

**422** · Cupón inválido — Cupón vencido, agotado, bajo el mínimo, solo para primer pedido o ya usado por el usuario.

### `DATOS_INVALIDOS`

**422** · Datos inválidos para la regla de negocio — Regla de negocio genérica sobre los datos.

### `DESTINO_REQUERIDO`

**422** · Falta el destino de la entrega — Entrega estudiante sin destino.

### `ORDEN_VACIA`

**422** · Orden vacía — Se intentó pagar una orden sin productos.

### `PERFIL_NO_ELEGIBLE`

**422** · Perfil no elegible — Perfil dual: faltan pedidos completados para vender (mínimo 3).

### `PRODUCTO_NO_ENCONTRADO`

**422** · Producto no disponible en este puesto — El producto no es del puesto o no está disponible.

### `RFC_INVALIDO`

**422** · RFC inválido — El RFC para la factura no tiene formato válido.

### `SIN_ENTREGA`

**422** · El puesto no ofrece entrega — El puesto solo ofrece pickup.

### `ERROR_INTERNO`

**500** · Error interno del servidor — Error inesperado del servidor (no expone detalles internos).
