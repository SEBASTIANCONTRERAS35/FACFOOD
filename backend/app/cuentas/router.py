"""Rebanada Cuentas (Sebastián): registro, login y perfil. Vista 01."""

from fastapi import APIRouter, Depends, status

from app.cuentas import servicio
from app.cuentas.esquemas import LoginEntrada, RegistroEntrada, SesionSalida, UsuarioSalida
from app.shared.auth import UsuarioActual, crear_token, get_usuario_actual
from app.shared.uow import FabricaUoW, obtener_fabrica_uow

router = APIRouter(tags=["Cuentas"])


def _sesion(cuenta) -> SesionSalida:
    return SesionSalida(access_token=crear_token(cuenta.id), usuario=servicio.resumen(cuenta))


@router.post("/auth/registro", response_model=SesionSalida, status_code=status.HTTP_201_CREATED,
             summary="Crear cuenta (requiere consentimiento LFPDPPP)")
def registro(datos: RegistroEntrada, fabrica: FabricaUoW = Depends(obtener_fabrica_uow)):
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
