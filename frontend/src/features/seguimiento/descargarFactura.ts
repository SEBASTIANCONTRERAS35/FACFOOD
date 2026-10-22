import {ApiError,sesion} from "../../api/client";
const BASE=(import.meta.env.VITE_API_URL as string|undefined)??"http://localhost:8000";
/** Descarga XML con el almacenamiento de sesión existente, sin cambiar el cliente compartido. */
export async function descargarFactura(id:number):Promise<void>{
 const headers:Record<string,string>={Accept:"application/xml"};const token=sesion.token();const prueba=sesion.usuarioPrueba();if(token)headers.Authorization=`Bearer ${token}`;else if(prueba)headers["X-Usuario-Id"]=prueba;
 let respuesta:Response;try{respuesta=await fetch(`${BASE}/ordenes/${id}/factura`,{headers});}catch{throw new ApiError(0,"No hay conexión con el servidor. ¿Está corriendo la API?");}
 if(!respuesta.ok){const d=await respuesta.json().catch(()=>null);throw new ApiError(respuesta.status,typeof d?.detail==="string"?d.detail:"No se pudo descargar la factura.",d?.codigo);}
 const url=URL.createObjectURL(await respuesta.blob());const a=document.createElement("a");a.href=url;a.download=`factura-facfood-${id}.xml`;a.click();URL.revokeObjectURL(url);
}
