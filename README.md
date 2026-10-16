# FACFOOD

Pedidos de comida dentro de Ciudad Universitaria (UNAM): los estudiantes encuentran puestos
cercanos, piden para recoger o con entrega por otro estudiante, y pagan con cupones y lealtad.

Proyecto del squad **Kora Bits** para Negocios Electrónicos y Desarrollo Web (2027-1).

- Arquitectura: [ADR 001](ADR_001.md) y [ADR 002](ADR_002.md)
- Contrato entre las dos mitades de la app: [docs/CONTRATO.md](docs/CONTRATO.md)
- Diseño de las 8 pantallas: [docs/diseno/](docs/diseno/)
- Bitácora por sprint: [docs/EVOLUCION.md](docs/EVOLUCION.md)
- Cómo trabajamos con ramas: [CONTRIBUTING.md](CONTRIBUTING.md)

## Estructura

```
backend/   API en FastAPI (Python 3.11+)
  app/domain/      reglas de negocio puras: usuario, entrega (Strategy), crm, erp
  app/ports/       interfaces de repositorio
  app/adapters/    memoria y postgres
  app/cuentas|catalogo|checkout/        vistas 01–04
  app/seguimiento|vendedor|entregas/    vistas 05–08
  migrations/      Alembic
  tests/           unit/ (dominio), api/, integracion/ (PostgreSQL)
frontend/  React + Vite + TypeScript
docs/      contrato, diseño y bitácora
```

## Correr la app sin base de datos (lo más rápido)

```bash
# Backend: datos de ejemplo en memoria
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload            # http://localhost:8000/docs

# Frontend (otra terminal)
cd frontend
npm install
npm run dev                              # http://localhost:5173
```

En desarrollo aparece un botón **DEV** arriba a la derecha para entrar como cualquier usuario de
ejemplo (comprador, vendedor o repartidor). Todos tienen la contraseña `facfood123`.

## Correr con PostgreSQL + PostGIS

```bash
docker compose up -d db
cd backend
export FACFOOD_REPOSITORIO=postgres
export DATABASE_URL=postgresql+psycopg://facfood:facfood@localhost:5432/facfood
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

## Pruebas

```bash
cd backend && pytest -m "not integracion"     # dominio y API (sin base de datos)
cd backend && pytest -m integracion           # requiere DATABASE_URL
cd frontend && npm test && npm run build
```

La CI (GitHub Actions) corre las tres: backend, integración con PostGIS y frontend.
