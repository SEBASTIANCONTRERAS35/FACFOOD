# Evolución del proyecto FACFOOD (Kora Bits)

Este documento muestra cómo fue creciendo el repositorio conforme el profesor
fue pidiendo cada entrega. Los archivos de entregas anteriores se conservan.

## Sprint 1 — Misión: el "guardián" (CI)
| Paso del reto | Archivo |
|---|---|
| Codificar la prueba (dominio puro) | `src/domain.py`, `tests/test_domain.py` |
| Construir el pipeline | `.github/workflows/ci.yml` |
| Enfrentar al guardián (Pull Request a `main`) | PR `sprint1-pr` con CI en verde |

Contenido: patrón **Strategy** para el método de entrega (`Pickup`, `EntregaEstudiante`).

## Sprint 2 — Los 4 pasos en `develop`
| Paso | Qué se hizo | Archivo |
|---|---|---|
| 1. Entidad de Dominio | Clase `Usuario` | `src/usuario.py` |
| 2. Regla Core de Negocio | Perfil Dual: comprador -> vendedor tras 3 pedidos | `src/usuario.py` |
| 3. LFPDPPP y Seguridad | Hash de contraseña con bcrypt (Art. 18) y bandera de consentimiento (Art. 7) | `src/usuario.py` |
| 4. Prueba Unitaria TDD | Pruebas en verde | `tests/test_usuario.py` |

El pipeline (`ci.yml`) ejecuta todas las pruebas: las de Sprint 1 y las de Sprint 2.

## Sprint 3 — Módulo CRM (gestión de usuarios: retención)
El CRM vive en su propia carpeta `crm/`, separada del núcleo (`src/`).

| Qué se hizo | Archivo |
|---|---|
| Cupones (porcentaje, vigencia, pedido mínimo, tope, usos máximos) | `crm/retencion.py` |
| Lealtad por nivel (bronce, plata, oro) y cupón de bienvenida | `crm/retencion.py` |
| Regla: los descuentos no se acumulan, se aplica el mayor | `crm/retencion.py` |
| Pruebas unitarias | `tests/test_crm.py` |

## Sprint 4 — Módulo ERP (órdenes, facturación y flujo financiero)
El ERP vive en `erp/` y usa los cupones del CRM.

| Qué se hizo | Archivo |
|---|---|
| Orden con líneas de pedido; el precio lo dicta el catálogo del servidor | `erp/orden.py` |
| Total = (Subtotal - Descuentos) + IVA 16% + Envío, con `Decimal` | `erp/orden.py` |
| Máquina de estados estricta: CREADA -> PAGADA -> EN_PREPARACION -> ENVIADA -> ENTREGADA (o CANCELADA) | `erp/orden.py` |
| Factura inmutable con folio y XML simplificado (sandbox), validación de RFC | `erp/factura.py` |
| Pago dividido entre plataforma y vendedor (marketplace) | `erp/orden.py` |
| Diagrama de clases y de estados | `erp/UML.md` |
| Pruebas unitarias | `tests/test_erp.py` |

## MVP — Estructura base de la app (ADR 002)
El dominio se movió a `backend/app/domain/` y alrededor se construyó la app hexagonal.

| Qué se hizo | Dónde |
|---|---|
| Puertos de persistencia y adaptadores en memoria y PostgreSQL + PostGIS | `backend/app/ports/`, `backend/app/adapters/` |
| Esquema completo con Alembic y datos de ejemplo de CU | `backend/migrations/`, `backend/app/seed.py` |
| Autenticación (JWT) y usuario de prueba para desarrollo | `backend/app/shared/auth.py` |
| Frontend React con los componentes del Figma | `frontend/src/components/` |
| Diseño de las 8 pantallas y contrato entre las dos mitades | `docs/diseno/`, `docs/CONTRATO.md` |
| CI con backend, integración con PostGIS y frontend | `.github/workflows/ci.yml` |

## Siguiente
- Vistas 01–04 (Sebastián) y 05–08 (Arturo), ver `docs/CONTRATO.md`
- Módulo SCM
