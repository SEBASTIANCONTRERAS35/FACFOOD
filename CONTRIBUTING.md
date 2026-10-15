# Cómo trabajamos en FACFOOD (Kora Bits)

## Ramas

| Rama | Para qué | Quién escribe |
|---|---|---|
| `main` | Lo entregado y revisado por el profesor | Solo por Pull Request desde `Develop` |
| `Develop` | Integración del equipo | Solo por Pull Request desde una rama `feature/` |
| `feature/<tema>` | Trabajo de cada quien (ej. `feature/api-usuarios`) | Su autor |

## Flujo

1. Actualiza tu copia: `git switch Develop && git pull`
2. Crea tu rama: `git switch -c feature/<tema>`
3. Haz commits pequeños con mensajes claros (qué y por qué).
4. Corre las pruebas antes de subir: `pip install pytest bcrypt` y `pytest tests/`
5. Sube tu rama: `git push -u origin feature/<tema>`
6. Abre un Pull Request hacia `Develop`. Se integra solo si la CI está en verde
   y otra persona del equipo lo revisó.

## Reglas

- **No subir archivos con "Add files via upload" desde la web de GitHub.** Así se
  borraron y renombraron archivos sin querer (por ejemplo `ci.yml`). Usa git.
- No hacer push directo a `main` ni a `Develop`.
- Todo código nuevo de dominio lleva su prueba en `tests/`.
- El dominio (`src/`, `crm/`, `erp/`) no importa base de datos ni frameworks
  (arquitectura hexagonal, ver `ADR_001.md`).
- Los finales de línea se normalizan a LF con `.gitattributes`; no lo cambies.
