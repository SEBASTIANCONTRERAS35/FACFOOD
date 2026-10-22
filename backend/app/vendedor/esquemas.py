from pydantic import BaseModel
class CambioEstadoEntrada(BaseModel):
 estado:str
class PuntoVentaEntrada(BaseModel):
 abierto:bool
class OrdenVendedor(BaseModel):
 id:int; estado:str; punto_venta_id:int; punto_venta:str; metodo_entrega:str; total:str; creada_en:str|None
class PuntoVentaPanel(BaseModel):
 id:int; nombre:str; abierto:bool
class PanelVendedor(BaseModel):
 ordenes:list[OrdenVendedor]
 puntos_venta:list[PuntoVentaPanel]
class PuntoVentaSalida(BaseModel):
 id:int; nombre:str; abierto:bool
