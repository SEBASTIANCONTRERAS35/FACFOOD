"""Casos de uso de cuentas: registro (LFPDPPP), login y perfil dual."""

from app.domain.crm.retencion import nivel_lealtad
from app.domain.usuario import Usuario
from app.ports.repositorios import CuentaUsuario
from app.shared.errores import Conflicto, NoAutenticado, NoEncontrado
from app.shared.uow import FabricaUoW

# Hash de una contraseña cualquiera: si el correo no existe se verifica contra él,
# para que la respuesta tarde lo mismo y no revele qué correos están registrados.
_USUARIO_SEÑUELO = Usuario("señuelo", "000000000", consentimiento_datos=True)
_USUARIO_SEÑUELO.registrar_password("contraseña-señuelo")


def registrar(fabrica: FabricaUoW, nombre: str, credencial: str, correo: str, password: str,
              consentimiento: bool) -> CuentaUsuario:
    # El dominio exige el consentimiento (Art. 7 LFPDPPP) antes que cualquier otra cosa.
    usuario = Usuario(nombre, credencial, consentimiento_datos=consentimiento)
    with fabrica() as uow:
        if uow.usuarios.por_correo(correo):
            raise Conflicto("Ya existe una cuenta con ese correo", "CORREO_REGISTRADO")
        if uow.usuarios.existe_credencial(credencial):
            raise Conflicto("Ese número de cuenta UNAM ya está registrado", "CREDENCIAL_REGISTRADA")
        usuario.registrar_password(password)  # solo se guarda el hash (Art. 18 LFPDPPP)
        cuenta = uow.usuarios.agregar(CuentaUsuario(None, correo, usuario))
        uow.commit()
        return cuenta


def autenticar(fabrica: FabricaUoW, correo: str, password: str) -> CuentaUsuario:
    with fabrica() as uow:
        cuenta = uow.usuarios.por_correo(correo)
    usuario = cuenta.usuario if cuenta else _USUARIO_SEÑUELO
    if not usuario.verificar_password(password) or cuenta is None:
        raise NoAutenticado("Correo o contraseña incorrectos", "CREDENCIALES_INVALIDAS")
    return cuenta


def obtener(fabrica: FabricaUoW, usuario_id: int) -> CuentaUsuario:
    with fabrica() as uow:
        cuenta = uow.usuarios.por_id(usuario_id)
    if cuenta is None:
        raise NoEncontrado("El usuario no existe")
    return cuenta


def convertirse_en_vendedor(fabrica: FabricaUoW, usuario_id: int) -> CuentaUsuario:
    with fabrica() as uow:
        cuenta = uow.usuarios.por_id(usuario_id)
        if cuenta.usuario.rol == "vendedor":
            return cuenta
        if cuenta.usuario.rol != "comprador":
            raise Conflicto("Solo una cuenta de comprador puede volverse vendedor", "ROL_INCOMPATIBLE")
        cuenta.usuario.convertirse_en_vendedor()  # perfil dual: mínimo 3 pedidos completados
        uow.usuarios.guardar(cuenta)
        uow.commit()
        return cuenta


def resumen(cuenta: CuentaUsuario) -> dict:
    u = cuenta.usuario
    return {
        "id": cuenta.id,
        "nombre": u.nombre,
        "correo": cuenta.correo,
        "rol": u.rol,
        "pedidos_completados": u.pedidos_completados,
        "nivel_lealtad": nivel_lealtad(u.pedidos_completados),
        "puede_vender": u.rol == "comprador"
        and u.pedidos_completados >= Usuario.PEDIDOS_MINIMOS_PARA_VENDEDOR,
    }
