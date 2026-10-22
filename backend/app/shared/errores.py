"""Errores de la aplicación y su traducción a respuestas HTTP.

Toda respuesta de error tiene la forma {"detail": "...", "codigo": "..."}.
"""

import re

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

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


def registrar_manejadores(app: FastAPI) -> None:
    async def de_aplicacion(_: Request, exc: ErrorDeAplicacion):
        return JSONResponse({"detail": exc.mensaje, "codigo": exc.codigo}, status_code=exc.status)

    app.add_exception_handler(ErrorDeAplicacion, de_aplicacion)

    async def de_validacion_entrega(request: Request, exc: RequestValidationError):
        if not re.fullmatch(r"/entregas/\d+/entregar", request.url.path):
            return await request_validation_exception_handler(request, exc)

        errores = exc.errors()
        for error in errores:
            if error.get("loc", ())[:2] == ("body", "codigo_entrega"):
                error.pop("input", None)
        return JSONResponse({"detail": jsonable_encoder(errores)}, status_code=422)

    app.add_exception_handler(RequestValidationError, de_validacion_entrega)

    for tipo, (status, codigo) in ERRORES_DE_DOMINIO.items():

        async def de_dominio(_: Request, exc: Exception, status=status, codigo=codigo):
            return JSONResponse({"detail": str(exc), "codigo": codigo}, status_code=status)

        app.add_exception_handler(tipo, de_dominio)
