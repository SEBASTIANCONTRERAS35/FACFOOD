# Desplegar FACFOOD (gratis, con HTTPS)

Guía para que cualquier integrante publique la app. Al terminar, FACFOOD queda en una
dirección `https://…vercel.app` que se puede abrir e **instalar en el celular** (PWA).

Tiempo: ~1 hora. Costo: $0 (planes gratuitos). Decisión y alternativas: [ADR 003](../ADR_003.md).

| Parte | Servicio | Qué se crea |
|---|---|---|
| Base de datos (PostgreSQL + PostGIS) | **Neon** | proyecto `facfood` |
| API (FastAPI) | **Render** | servicio web `facfood-api` |
| Frontend (PWA) | **Vercel** | proyecto `facfood` |

> **Importante:** el orden es Neon → Render → Vercel → (volver a Render para el CORS),
> porque cada paso necesita la dirección del anterior.

## 0. Antes de empezar

- Tener cuenta de GitHub con acceso al repo `SEBASTIANCONTRERAS35/FACFOOD`.
- Las tres cuentas se crean **con ese GitHub** ("Continue with GitHub"). Ninguna pide tarjeta.
- Se despliega la rama **`main`**: lo que esté en `main` es lo que se publica.

## 1. Neon: la base de datos

1. Entra a <https://neon.tech> → **Sign up** con GitHub.
2. **Create project**: nombre `facfood`, Postgres 16, región **AWS US East (Ohio)**
   (la más cercana a Render en EE. UU.).
3. En el panel del proyecto, **Connect** → copia la **Connection string**. Se ve así:
   ```
   postgresql://usuario:clave@ep-xxxx.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
   Guárdala: es el `DATABASE_URL`. **No la compartas ni la subas al repo** (trae la contraseña).

No hace falta crear tablas ni activar PostGIS: la API lo hace sola al arrancar
(`alembic upgrade head` ejecuta `CREATE EXTENSION postgis`).

## 2. Render: la API

1. Entra a <https://render.com> → **Get Started** con GitHub y autoriza el acceso al repo.
2. **New → Blueprint** → elige el repo `FACFOOD`. Render lee [`render.yaml`](../render.yaml) y
   propone el servicio `facfood-api` en el plan **Free**.
3. Te pide dos valores:
   - `DATABASE_URL` → la cadena de Neon del paso 1.
   - `FACFOOD_CORS` → por ahora escribe `https://pendiente.vercel.app` (se corrige en el paso 4).
4. **Apply**. El primer despliegue tarda unos 5 minutos.
5. Copia la dirección del servicio (p. ej. `https://facfood-api.onrender.com`) y comprueba:
   - `https://facfood-api.onrender.com/salud` → `{"estado":"ok","repositorio":"postgres"}`
   - `https://facfood-api.onrender.com/docs` → la documentación de la API (Swagger).

El secreto de los JWT lo genera Render solo (`FACFOOD_JWT_SECRETO`), y el usuario de prueba
queda apagado (`FACFOOD_PERMITIR_USUARIO_PRUEBA=false`).

## 3. Vercel: el frontend

1. Entra a <https://vercel.com> → **Sign up** con GitHub (plan **Hobby**, gratis).
2. **Add New → Project** → importa el repo `FACFOOD`.
3. Configuración:
   - **Root Directory:** `frontend`  ← importante
   - **Framework Preset:** Vite (lo detecta solo; el resto viene de [`frontend/vercel.json`](../frontend/vercel.json))
   - **Environment Variables:** `VITE_API_URL` = la dirección de Render del paso 2, **sin `/` al final**
     (p. ej. `https://facfood-api.onrender.com`).
4. **Deploy**. Copia la dirección final (p. ej. `https://facfood.vercel.app`).
5. En **Settings → Git**, confirma que la **Production Branch** sea `main`.

## 4. Volver a Render: permitir al frontend (CORS)

1. En Render → `facfood-api` → **Environment** → cambia `FACFOOD_CORS` por la dirección de
   Vercel del paso 3, **sin `/` al final** (p. ej. `https://facfood.vercel.app`).
   Si hay más de una, sepáralas con coma.
2. **Save changes** (Render vuelve a desplegar solo).

## 5. Comprobar que todo funciona

- [ ] `https://…vercel.app` abre el registro de FACFOOD con candado (HTTPS).
- [ ] Iniciar sesión con `diana@facfood.mx` / `facfood123` y ver los puestos en el mapa.
- [ ] Pedir en *Tacos Don Memo*, aplicar `BIENVENIDA15` y pagar: llega al seguimiento.
- [ ] **Android (Chrome):** aparece "Instala FACFOOD" en Explorar → *Instalar*.
- [ ] **iPhone (Safari):** *Compartir → Agregar a inicio*. Se abre a pantalla completa.
- [ ] Con la app instalada y en modo avión, abre y muestra los puestos ya vistos.

Usuarios de ejemplo (todos con contraseña `facfood123`): `diana@facfood.mx` (comprador),
`sebastian@facfood.mx` (comprador, nivel plata), `memo@facfood.mx` (vendedor),
`lupita@facfood.mx` (vendedor), `arturo@facfood.mx` (repartidor).

## 6. Lo que hay que saber

- **La API se duerme** en el plan gratis tras ~15 min sin uso: la primera petición después
  tarda 30–60 s. Antes de una demo, abre `/salud` un minuto antes.
- **Actualizaciones:** cada push a `main` se despliega solo en Render y en Vercel. La PWA
  instalada muestra "Hay una versión nueva · Actualizar".
- **Datos:** los de ejemplo se cargan una sola vez (si la base está vacía). Lo que creen los
  usuarios se guarda en Neon.
- **Quién administra:** las cuentas son de quien las creó. Para que otro integrante pueda
  entrar, invítenlo en cada servicio (Neon: *Settings → Members*; Render y Vercel: el plan
  gratis es personal, compartan la sesión o transfieran el proyecto si hace falta).
- **No subir secretos al repo:** `DATABASE_URL` y `FACFOOD_JWT_SECRETO` viven solo en Render.

## 7. Si algo falla

| Síntoma | Causa probable | Solución |
|---|---|---|
| El frontend dice "No hay conexión con el servidor" | La API está dormida o `VITE_API_URL` está mal | Abre `/salud` de la API; revisa la variable en Vercel y vuelve a desplegar |
| En la consola del navegador: error de **CORS** | `FACFOOD_CORS` no coincide con el dominio de Vercel | Copia el dominio exacto, sin `/` final (paso 4) |
| "Mixed content" o no carga nada | `VITE_API_URL` empieza con `http://` | Debe ser `https://…onrender.com` |
| Al recargar una página sale 404 | El proyecto de Vercel no usa `frontend` como raíz | *Settings → General → Root Directory* = `frontend` |
| Render falla con `relation ... does not exist` | No corrió la migración | Revisa el *Start Command* del `render.yaml` y los logs del despliegue |
| Render falla al conectar a la base | `DATABASE_URL` incompleta | Debe incluir `?sslmode=require` (viene así desde Neon) |
| No aparece "Instalar" en el celular | La página no está en HTTPS o ya está instalada | Usa la dirección `https://…vercel.app` |
