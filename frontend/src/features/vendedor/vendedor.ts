export type OrdenVendedor={id:number;estado:string;punto_venta_id:number;punto_venta:string;metodo_entrega:"pickup"|"estudiante";total:string;creada_en:string|null};
export const siguienteEstado=(e:string,m:string)=>e==="PAGADA"?"EN_PREPARACION":e==="EN_PREPARACION"&&m==="pickup"?"ENVIADA":e==="ENVIADA"&&m==="pickup"?"ENTREGADA":null;
export const textoAccion=(e:string)=>e==="PAGADA"?"Iniciar preparación":e==="EN_PREPARACION"?"Marcar listo para recoger":"Entregado al cliente";
