"""Errores de la aplicación y su traducción a respuestas HTTP (RFC 7807, Problem Details).

Toda respuesta de error es `application/problem+json`:
    {"type", "title", "status", "detail", "instance", "codigo"}
y, si falló la validación de un DTO (400), además `invalid_params: [{name, reason}]`.

- 400 el JSON o los parámetros no cumplen el esquema del DTO (Pydantic)
- 401 sin sesión · 403 sin el rol · 404 no existe
- 409 conflicto con el estado actual (pagar dos veces, transición inválida)
- 422 la petición es válida pero rompe una regla de negocio (cupón vencido, puesto sin entrega)

Por seguridad, ningún error repite lo que envió el usuario (contraseñas, códigos de entrega).
Catálogo de códigos: docs/ERRORES.md.
"""

from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.domain.crm.retencion import CuponInvalidoError
from app.domain.erp.factura import RfcInvalidoError
from app.domain.erp.orden import (
    FacturaNoPermitidaError,
    InvalidStateTransitionException,
    OrdenInmutableError,
    OrdenNoPagadaError,
    OrdenVaciaError,
    ProductoNoEncontradoError,
)
from app.domain.usuario import ConsentimientoRequeridoError, PerfilNoElegibleError

TIPOS = "https://github.com/SEBASTIANCONTRERAS35/FACFOOD/blob/main/docs/ERRORES.md"
MEDIA_PROBLEMA = "application/problem+json"


class ErrorDeAplicacion(Exception):
    status = 400
    codigo = "ERROR"

    def __init__(self, mensaje: str, codigo: str | None = None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        if codigo:
            self.codigo = codigo


class NoEncontrado(ErrorDeAplicacion):
    status = 404
    codigo = "NO_ENCONTRADO"


class Conflicto(ErrorDeAplicacion):
    status = 409
    codigo = "CONFLICTO"


class NoAutenticado(ErrorDeAplicacion):
    status = 401
    codigo = "NO_AUTENTICADO"


class Prohibido(ErrorDeAplicacion):
    status = 403
    codigo = "PROHIBIDO"


class DatosInvalidos(ErrorDeAplicacion):
    status = 422
    codigo = "DATOS_INVALIDOS"


# Excepciones del dominio -> (status HTTP, código)
ERRORES_DE_DOMINIO = {
    ConsentimientoRequeridoError: (422, "CONSENTIMIENTO_REQUERIDO"),
    PerfilNoElegibleError: (422, "PERFIL_NO_ELEGIBLE"),
    CuponInvalidoError: (422, "CUPON_INVALIDO"),
    InvalidStateTransitionException: (409, "TRANSICION_INVALIDA"),
    OrdenInmutableError: (409, "ORDEN_INMUTABLE"),
    OrdenVaciaError: (422, "ORDEN_VACIA"),
    ProductoNoEncontradoError: (422, "PRODUCTO_NO_ENCONTRADO"),
    FacturaNoPermitidaError: (409, "FACTURA_NO_PERMITIDA"),
    OrdenNoPagadaError: (409, "ORDEN_NO_PAGADA"),
    RfcInvalidoError: (422, "RFC_INVALIDO"),
}

# Título fijo por tipo de problema (RFC 7807: el título no cambia entre ocurrencias).
TITULOS = {
    "VALIDACION": "Error de validación en los datos de entrada",
    "NO_AUTENTICADO": "Se requiere iniciar sesión",
    "CREDENCIALES_INVALIDAS": "Credenciales inválidas",
    "PROHIBIDO": "No tienes permiso para esta acción",
    "NO_ENCONTRADO": "Recurso no encontrado",
    "RUTA_NO_ENCONTRADA": "Ruta no encontrada",
    "CUPON_INEXISTENTE": "Cupón no encontrado",
    "CONFLICTO": "Conflicto con el estado actual",
    "CORREO_REGISTRADO": "Correo ya registrado",
    "CREDENCIAL_REGISTRADA": "Número de cuenta ya registrado",
    "CUENTA_DUPLICADA": "Cuenta duplicada",
    "ROL_INCOMPATIBLE": "Rol incompatible",
    "PUESTO_CERRADO": "Puesto cerrado",
    "ORDEN_YA_PAGADA": "Orden ya pagada",
    "TRANSICION_INVALIDA": "Transición de estado inválida",
    "TRANSICION_NO_AUTORIZADA": "Transición de estado no autorizada",
    "ORDEN_INMUTABLE": "La orden ya no se puede modificar",
    "FACTURA_NO_PERMITIDA": "Factura no permitida",
    "ORDEN_NO_PAGADA": "La orden no está pagada",
    "ENTREGA_YA_ACEPTADA": "Entrega ya aceptada",
    "ENTREGA_NO_DISPONIBLE": "Entrega no disponible",
    "ESTADO_ENTREGA_INVALIDO": "Estado de entrega inválido",
    "ORDEN_PENDIENTE_PREPARACION": "Orden pendiente de preparación",
    "DATOS_INVALIDOS": "Datos inválidos para la regla de negocio",
    "CONSENTIMIENTO_REQUERIDO": "Se requiere consentimiento (LFPDPPP)",
    "PERFIL_NO_ELEGIBLE": "Perfil no elegible",
    "CUPON_INVALIDO": "Cupón inválido",
    "ORDEN_VACIA": "Orden vacía",
    "PRODUCTO_NO_ENCONTRADO": "Producto no disponible en este puesto",
    "RFC_INVALIDO": "RFC inválido",
    "SIN_ENTREGA": "El puesto no ofrece entrega",
    "DESTINO_REQUERIDO": "Falta el destino de la entrega",
    "CODIGO_ENTREGA_INVALIDO": "Código de entrega inválido",
    "METODO_NO_PERMITIDO": "Método HTTP no permitido",
    "ERROR_INTERNO": "Error interno del servidor",
}


# ---- Esquemas para la documentación (Swagger) ----
class ParametroInvalido(BaseModel):
    name: str = Field(description="Campo que no cumple la regla (ej. `lineas.0.cantidad`)")
    reason: str = Field(description="Qué regla no cumple, en español")


class Problema(BaseModel):
    """Error en formato RFC 7807 (Problem Details)."""

    type: str = Field(description="URI que documenta el tipo de problema")
    title: str = Field(description="Resumen fijo del tipo de problema")
    status: int = Field(description="Código HTTP")
    detail: str = Field(description="Explicación de esta ocurrencia, para mostrar al usuario")
    instance: str = Field(description="Ruta de la petición que falló")
    codigo: str = Field(description="Código estable para que el frontend reaccione (ver docs/ERRORES.md)")


class ProblemaValidacion(Problema):
    """Error 400: el DTO de entrada no cumple su esquema."""

    invalid_params: list[ParametroInvalido]


def ejemplo_problema(status: int, codigo: str, detail: str, instance: str, **extra) -> dict:
    return {
        "type": f"{TIPOS}#{codigo.lower()}", "title": TITULOS.get(codigo, HTTPStatus(status).phrase),
        "status": status, "detail": detail, "instance": instance, "codigo": codigo, **extra,
    }


def respuesta_error(status: int, codigo: str, detail: str, instance: str, **extra) -> dict:
    """Para `responses=` de un router: documenta un error con su ejemplo."""
    modelo = ProblemaValidacion if "invalid_params" in extra else Problema
    return {"model": modelo, "description": TITULOS.get(codigo, HTTPStatus(status).phrase),
            "content": {"application/json": {"example": ejemplo_problema(status, codigo, detail, instance, **extra)}}}


# ---- Respuestas ----
def _problema(request: Request, status: int, codigo: str, detail: str, **extra) -> JSONResponse:
    return JSONResponse(
        ejemplo_problema(status, codigo, detail, request.url.path, **extra),
        status_code=status, media_type=MEDIA_PROBLEMA,
    )


def _nombre_campo(loc) -> str:
    # ("body", "lineas", 0, "cantidad") -> "lineas.0.cantidad"; ("query", "lat") -> "lat"
    partes = [str(p) for p in loc]
    if partes and partes[0] in {"body", "query", "path", "header", "cookie"}:
        partes = partes[1:]
    return ".".join(partes) or "body"


def _motivo(error: dict) -> str:
    mensaje = error.get("msg", "Valor inválido")
    return mensaje.removeprefix("Value error, ")


def registrar_manejadores(app: FastAPI) -> None:
    async def de_aplicacion(request: Request, exc: ErrorDeAplicacion):
        return _problema(request, exc.status, exc.codigo, exc.mensaje)

    async def de_validacion(request: Request, exc: RequestValidationError):
        # Nunca se incluye `input`: el valor enviado puede ser una contraseña o un código de entrega.
        parametros = [{"name": _nombre_campo(e.get("loc", ())), "reason": _motivo(e)} for e in exc.errors()]
        return _problema(
            request, 400, "VALIDACION",
            "Uno o más campos del payload no cumplen con las reglas establecidas.",
            invalid_params=parametros,
        )

    async def de_http(request: Request, exc: StarletteHTTPException):
        if exc.status_code == 404:
            return _problema(request, 404, "RUTA_NO_ENCONTRADA", "Esa ruta no existe en la API.")
        if exc.status_code == 405:
            return _problema(request, 405, "METODO_NO_PERMITIDO", "Esa ruta no acepta este método HTTP.")
        return _problema(request, exc.status_code, "ERROR", str(exc.detail))

    async def inesperado(request: Request, exc: Exception):
        return _problema(request, 500, "ERROR_INTERNO", "Ocurrió un error inesperado. Intenta de nuevo.")

    app.add_exception_handler(ErrorDeAplicacion, de_aplicacion)
    app.add_exception_handler(RequestValidationError, de_validacion)
    app.add_exception_handler(StarletteHTTPException, de_http)
    app.add_exception_handler(Exception, inesperado)

    for tipo, (status, codigo) in ERRORES_DE_DOMINIO.items():

        async def de_dominio(request: Request, exc: Exception, status=status, codigo=codigo):
            return _problema(request, status, codigo, str(exc))

        app.add_exception_handler(tipo, de_dominio)


def documentar_errores(app: FastAPI) -> None:
    """Ajusta la especificación OpenAPI al formato real de los errores:
    - quita el 422 genérico de FastAPI (HTTPValidationError), porque respondemos 400 RFC 7807;
    - agrega el 400 de validación a cada operación que recibe datos;
    - publica todos los errores como `application/problem+json`."""
    original = app.openapi

    def openapi():
        if app.openapi_schema:
            return app.openapi_schema
        esquema = original()
        componentes = esquema.setdefault("components", {}).setdefault("schemas", {})
        definiciones = ProblemaValidacion.model_json_schema(ref_template="#/components/schemas/{model}")
        componentes.update(definiciones.pop("$defs", {}))
        componentes["ProblemaValidacion"] = definiciones
        componentes.setdefault("Problema", Problema.model_json_schema(ref_template="#/components/schemas/{model}"))
        ref_validacion = {"$ref": "#/components/schemas/ProblemaValidacion"}

        for ruta, operaciones in esquema.get("paths", {}).items():
            for operacion in operaciones.values():
                respuestas = operacion.get("responses", {})
                generico = respuestas.get("422", {})
                if "HTTPValidationError" in str(generico):
                    del respuestas["422"]
                    respuestas.setdefault("400", {
                        "description": TITULOS["VALIDACION"],
                        "content": {"application/json": {"schema": ref_validacion, "example": ejemplo_problema(
                            400, "VALIDACION", "Uno o más campos del payload no cumplen con las reglas establecidas.",
                            ruta, invalid_params=[{"name": "campo", "reason": "Descripción del error específico"}],
                        )}},
                    })
                for codigo_http, respuesta in respuestas.items():
                    contenido = respuesta.get("content", {})
                    if codigo_http.startswith(("4", "5")) and "application/json" in contenido:
                        contenido[MEDIA_PROBLEMA] = contenido.pop("application/json")
        for sobrante in ("HTTPValidationError", "ValidationError"):
            componentes.pop(sobrante, None)
        app.openapi_schema = esquema
        return esquema

    app.openapi = openapi
