export type MetodoEntrega = "pickup" | "estudiante";
export type EstadoPaso = "hecho" | "actual" | "pendiente";
const TITULOS: Record<string,string> = { CREADA:"Creada", PAGADA:"Pagada", EN_PREPARACION:"En preparación", ENVIADA:"Enviada", ENTREGADA:"Entregada", CANCELADA:"Cancelada" };
export function tituloEstado(estado:string):string { return TITULOS[estado] ?? estado; }
export function detalleEvento(estado:string, metodo:MetodoEntrega):string|undefined {
 if(estado==="PAGADA") return "Factura disponible"; if(estado==="EN_PREPARACION") return "El puesto está preparando tu pedido";
 if(estado==="ENVIADA") return metodo==="pickup" ? "Listo para recoger en el puesto" : "El repartidor ya lo recogió y va en camino";
 if(estado==="ENTREGADA") return "Pedido entregado"; if(estado==="CANCELADA") return "Pedido cancelado"; return undefined;
}
export function estadoPaso(actual:boolean,terminal:boolean,indice:number,total:number):EstadoPaso { if(actual)return "actual"; if(terminal||indice<total-1)return "hecho"; return "pendiente"; }
export function horaLocal(fecha:string):string { const d=new Date(fecha); return Number.isNaN(d.getTime()) ? "" : new Intl.DateTimeFormat("es-MX",{hour:"2-digit",minute:"2-digit"}).format(d); }
