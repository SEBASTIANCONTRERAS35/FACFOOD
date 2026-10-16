"""Solo desarrollo: lista los usuarios de ejemplo para el selector del frontend.

Se monta únicamente si FACFOOD_PERMITIR_USUARIO_PRUEBA=true.
"""

from fastapi import APIRouter, Depends

from app.shared.uow import FabricaUoW, obtener_fabrica_uow

router = APIRouter(prefix="/dev", tags=["Desarrollo"])


@router.get("/usuarios")
def usuarios_de_prueba(fabrica: FabricaUoW = Depends(obtener_fabrica_uow)):
    with fabrica() as uow:
        return [
            {"id": c.id, "nombre": c.usuario.nombre, "correo": c.correo, "rol": c.usuario.rol}
            for c in uow.usuarios.listar()
        ]
