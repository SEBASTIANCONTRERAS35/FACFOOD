"""Casos de uso de seguimiento y descarga de factura."""
from app.ports.repositorios import OrdenRegistro, UnidadDeTrabajo
from app.shared.auth import UsuarioActual
from app.shared.errores import NoEncontrado
from app.shared.presentacion import orden_a_json
from app.shared.uow import FabricaUoW
def _orden_propia(uow: UnidadDeTrabajo, orden_id: int, actual: UsuarioActual) -> OrdenRegistro:
    registro = uow.ordenes.por_id(orden_id)
    if registro is None or registro.comprador_id != actual.id:
        raise NoEncontrado("Esa orden no existe")
    return registro
def seguimiento(fabrica: FabricaUoW, actual: UsuarioActual, orden_id: int) -> dict:
    with fabrica() as uow:
        registro = _orden_propia(uow, orden_id, actual)
        salida = orden_a_json(uow, registro, actual.id)
        codigo = registro.codigo_entrega
        valido = registro.metodo_entrega == "estudiante" and registro.orden.estado.value != "CREADA" and codigo is not None and len(codigo) == 4 and codigo.isascii() and codigo.isdigit()
        if not valido:
            salida["codigo_entrega"] = None
        salida["eventos"] = [{"estado": e.estado, "actor_id": e.actor_id, "creado_en": e.creado_en} for e in uow.eventos.de_orden(orden_id)]
        return salida
def factura_xml(fabrica: FabricaUoW, actual: UsuarioActual, orden_id: int) -> bytes:
    with fabrica() as uow:
        _orden_propia(uow, orden_id, actual)
        factura = uow.facturas.de_orden(orden_id)
        if factura is None:
            raise NoEncontrado("La factura de este pedido aún no está disponible")
        return factura.factura.xml_data
