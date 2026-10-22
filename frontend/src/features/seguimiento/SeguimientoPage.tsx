import {useEffect,useState} from "react";
import {Link,useParams} from "react-router-dom";
import {api,ApiError} from "../../api/client";
import {pesos} from "../../api/dinero";
import {Boton,Pantalla,PasoEstado,Tarjeta} from "../../components";
import {useSesion} from "../cuenta/sesion";
import {descargarFactura} from "./descargarFactura";
import {detalleEvento,estadoPaso,horaLocal,tituloEstado} from "./seguimiento";
import "./seguimiento.css";
type Evento={estado:string;actor_id:number|null;creado_en:string};
type Seguimiento={id:number;estado:string;comprador_id:number;punto_venta:{id:number;nombre:string};metodo_entrega:"pickup"|"estudiante";total:string;codigo_entrega:string|null;factura_folio:string|null;eventos:Evento[]};
export function SeguimientoPage(){
 const {id:idTexto}=useParams(); const id=Number(idTexto); const {usuario}=useSesion();
 const [pedido,setPedido]=useState<Seguimiento|null>(null); const [error,setError]=useState(""); const [errorFactura,setErrorFactura]=useState(""); const [descargando,setDescargando]=useState(false);
 useEffect(()=>{if(!Number.isSafeInteger(id)||id<1){setError("Ese pedido no existe");return;} if(!usuario||usuario.rol!=="comprador")return;
  const c=new AbortController(); setPedido(null);setError(""); api<Seguimiento>(`/ordenes/${id}`,{signal:c.signal}).then(setPedido).catch(e=>{if((e as Error).name!=="AbortError")setError((e as ApiError).message);});return()=>c.abort();},[id,usuario]);
 async function bajarFactura(){setDescargando(true);setErrorFactura("");try{await descargarFactura(id);}catch(e){setErrorFactura((e as Error).message);}finally{setDescargando(false);}}
 if(usuario&&usuario.rol!=="comprador")return <Pantalla nav><div className="seccion seguimiento__mensaje"><p className="error-campo" role="alert">Esta pantalla es para la cuenta compradora.</p></div></Pantalla>;
 if(!pedido&&!error)return <Pantalla nav><div className="seccion seguimiento__mensaje"><p className="texto-muted" role="status">Cargando pedido…</p></div></Pantalla>;
 if(error||!pedido)return <Pantalla nav><div className="seccion seguimiento__mensaje"><h1>Pedido no disponible</h1><p className="error-campo" role="alert">{error||"No se pudo cargar el pedido."}</p><Link to="/explorar">Volver a explorar</Link></div></Pantalla>;
 const terminal=pedido.estado==="ENTREGADA"||pedido.estado==="CANCELADA";
 return <Pantalla nav><header className="seguimiento__encabezado"><h1>Pedido #{pedido.id}</h1><p>{pedido.punto_venta.nombre} · {pedido.metodo_entrega==="pickup"?"Pickup":"Entrega estudiante"} · Total {pesos(pedido.total)}</p></header>
 <div className="seccion seguimiento"><Tarjeta className="seguimiento__timeline">{pedido.eventos.map((e,i)=><PasoEstado key={`${e.estado}-${e.creado_en}-${i}`} estado={estadoPaso(!terminal&&e.estado===pedido.estado,terminal,i,pedido.eventos.length)} titulo={tituloEstado(e.estado)} detalle={[horaLocal(e.creado_en),detalleEvento(e.estado,pedido.metodo_entrega)].filter(Boolean).join(" · ")||undefined}/>)}{pedido.eventos.length===0&&<p className="texto-muted">Aún no hay eventos para este pedido.</p>}</Tarjeta>
 {pedido.metodo_entrega==="estudiante"&&pedido.codigo_entrega&&<Tarjeta className="seguimiento__codigo"><h2>Código de entrega</h2><p>Compártelo con tu repartidor cuando recibas el pedido.</p><strong aria-label="Código de entrega">{pedido.codigo_entrega}</strong></Tarjeta>}
 {pedido.factura_folio?<div><Boton variante="secundario" onClick={bajarFactura} cargando={descargando}>Descargar factura (sandbox)</Boton>{errorFactura&&<p className="error-campo" role="alert">{errorFactura}</p>}</div>:<p className="texto-muted">La factura estará disponible cuando se pague el pedido.</p>}</div></Pantalla>;
}
