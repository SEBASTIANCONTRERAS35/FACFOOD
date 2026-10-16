"""Quién es el usuario de la petición. Lo usan todas las rebanadas.

CONTRATO: la firma de get_usuario_actual() y UsuarioActual no cambian.
- Con encabezado `Authorization: Bearer <jwt>` se valida el token.
- En desarrollo (FACFOOD_PERMITIR_USUARIO_PRUEBA=true) también se acepta
  `X-Usuario-Id: <id>` para entrar como un usuario de ejemplo sin login.
El rol se lee de la base en cada petición, así el perfil dual aplica al momento.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, Header

from app.shared.config import obtener_config
from app.shared.errores import NoAutenticado, Prohibido
from app.shared.uow import FabricaUoW, obtener_fabrica_uow


@dataclass(frozen=True)
class UsuarioActual:
    id: int
    rol: str  # "comprador" | "vendedor" | "repartidor"


def crear_token(usuario_id: int) -> str:
    config = obtener_config()
    ahora = datetime.now(timezone.utc)
    datos = {"sub": str(usuario_id), "iat": ahora, "exp": ahora + timedelta(hours=config.jwt_horas)}
    return jwt.encode(datos, config.jwt_secreto, algorithm="HS256")


def _id_desde_token(token: str) -> int:
    try:
        datos = jwt.decode(token, obtener_config().jwt_secreto, algorithms=["HS256"])
        return int(datos["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise NoAutenticado("Sesión inválida o vencida; vuelve a iniciar sesión")


def get_usuario_actual(
    authorization: str | None = Header(default=None),
    x_usuario_id: int | None = Header(default=None),
    fabrica: FabricaUoW = Depends(obtener_fabrica_uow),
) -> UsuarioActual:
    if authorization and authorization.lower().startswith("bearer "):
        usuario_id = _id_desde_token(authorization.split(" ", 1)[1].strip())
    elif x_usuario_id is not None and obtener_config().permitir_usuario_prueba:
        usuario_id = x_usuario_id
    else:
        raise NoAutenticado("Inicia sesión para continuar")

    with fabrica() as uow:
        cuenta = uow.usuarios.por_id(usuario_id)
    if cuenta is None:
        raise NoAutenticado("El usuario de la sesión ya no existe")
    return UsuarioActual(cuenta.id, cuenta.usuario.rol)


def exigir_rol(*roles: str):
    """Dependencia: `Depends(exigir_rol("vendedor"))`."""

    def verificar(usuario: UsuarioActual = Depends(get_usuario_actual)) -> UsuarioActual:
        if usuario.rol not in roles:
            raise Prohibido(f"Esta acción requiere el rol: {', '.join(roles)}")
        return usuario

    return verificar
