"""Rebanada Cuentas (Sebastián): registro, login y perfil. Vista 01."""

from fastapi import APIRouter, Depends, status

from app.cuentas import servicio
from app.cuentas.esquemas import LoginEntrada, RegistroEntrada, SesionSalida, UsuarioSalida
from app.shared.auth import UsuarioActual, crear_token, get_usuario_actual
from app.shared.errores import respuesta_error
from app.shared.uow import FabricaUoW, obtener_fabrica_uow

router = APIRouter(tags=["Cuentas"])


def _sesion(cuenta) -> SesionSalida:
    return SesionSalida(access_token=crear_token(cuenta.id), usuario=servicio.resumen(cuenta))


@router.post(
    "/auth/registro", response_model=SesionSalida, status_code=status.HTTP_201_CREATED,
    summary="Crear cuenta (requiere consentimiento LFPDPPP)",
    responses={
        400: respuesta_error(400, "VALIDACION", "Uno o más campos del payload no cumplen con las reglas establecidas.",
                             "/auth/registro", invalid_params=[
                                 {"name": "credencial_unam", "reason": "El número de cuenta UNAM tiene 9 dígitos"},
                                 {"name": "password", "reason": "La contraseña debe tener al menos 8 caracteres"}]),
        409: respuesta_error(409, "CORREO_REGISTRADO", "Ya existe una cuenta con ese correo", "/auth/registro"),
        422: respuesta_error(422, "CONSENTIMIENTO_REQUERIDO",
                             "No se puede registrar al usuario sin su consentimiento de datos (Art. 7 LFPDPPP)",
                             "/auth/registro"),
    },
)
def registro(datos: RegistroEntrada, fabrica: FabricaUoW = Depends(obtener_fabrica_uow)):
    """Valida el DTO (400), exige el consentimiento del Art. 7 LFPDPPP (422) y guarda solo el hash
    bcrypt de la contraseña (Art. 18). La respuesta nunca incluye la contraseña ni su hash."""
    cuenta = servicio.registrar(
        fabrica, datos.nombre, datos.credencial_unam, datos.correo, datos.password,
        datos.consentimiento_datos,
    )
    return _sesion(cuenta)


@router.post("/auth/login", response_model=SesionSalida, summary="Iniciar sesión")
def login(datos: LoginEntrada, fabrica: FabricaUoW = Depends(obtener_fabrica_uow)):
    return _sesion(servicio.autenticar(fabrica, datos.correo, datos.password))


@router.get("/usuarios/me", response_model=UsuarioSalida, summary="Mi perfil")
def yo(actual: UsuarioActual = Depends(get_usuario_actual),
       fabrica: FabricaUoW = Depends(obtener_fabrica_uow)):
    return servicio.resumen(servicio.obtener(fabrica, actual.id))


@router.post("/usuarios/me/vendedor", response_model=UsuarioSalida,
             summary="Perfil dual: volverse vendedor (mínimo 3 pedidos)")
def volverse_vendedor(actual: UsuarioActual = Depends(get_usuario_actual),
                      fabrica: FabricaUoW = Depends(obtener_fabrica_uow)):
    return servicio.resumen(servicio.convertirse_en_vendedor(fabrica, actual.id))
