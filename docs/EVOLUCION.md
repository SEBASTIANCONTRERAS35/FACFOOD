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

## Siguiente
- Módulo SCM
- Reorganización de carpetas
