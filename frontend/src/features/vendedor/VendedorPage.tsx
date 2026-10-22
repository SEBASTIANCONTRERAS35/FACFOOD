import {useEffect,useState} from "react";
import {api,ApiError} from "../../api/client";
import {Boton,Pantalla,Tarjeta} from "../../components";
import {siguienteEstado,textoAccion,type OrdenVendedor} from "./vendedor";
import "./vendedor.css";
type Punto={id:number;nombre:string;abierto:boolean};
export function VendedorPage(){const [ordenes,setOrdenes]=useState<OrdenVendedor[]>([]),[puntos,setPuntos]=useState<Punto[]>([]),[error,setError]=useState(""),[busy,setBusy]=useState(true);
async function cargar(){try{const r=await api<{ordenes:OrdenVendedor[];puntos_venta:Punto[]}>("/vendedor/ordenes");setOrdenes(r.ordenes);setPuntos(r.puntos_venta);setError("")}catch(e){setError(e instanceof ApiError?e.message:"Error al cargar pedidos")}finally{setBusy(false)}}
useEffect(()=>{void cargar()},[]);
async function avanzar(o:OrdenVendedor){const estado=siguienteEstado(o.estado,o.metodo_entrega);if(!estado)return;try{await api(`/ordenes/${o.id}/estado`,{method:"POST",body:{estado}});await cargar()}catch(e){setError(e instanceof ApiError?e.message:"Error al actualizar")}}
async function alternar(p:Punto){try{await api(`/puntos-venta/${p.id}`,{method:"PATCH",body:{abierto:!p.abierto}});await cargar()}catch(e){setError(e instanceof ApiError?e.message:"Error al actualizar el puesto")}}
return <Pantalla><header className="vendedor__header"><h1>Panel del vendedor</h1></header>{error&&<p role="alert">{error}</p>}{puntos.map(p=><Tarjeta key={p.id}><div className="vendedor__puesto"><h2>{p.nombre}</h2><p>{p.abierto?"Abierto":"Cerrado"}</p><Boton variante="secundario" onClick={()=>void alternar(p)}>{p.abierto?"Cerrar puesto":"Abrir puesto"}</Boton></div></Tarjeta>)}{busy?<p>Cargando pedidos…</p>:ordenes.length===0?<p>No hay pedidos pendientes.</p>:<div className="vendedor__lista">{ordenes.map(o=><Tarjeta key={o.id}><article><h2>Pedido #{o.id}</h2><p>{o.punto_venta} · {o.metodo_entrega==="pickup"?"Recoger en puesto":"Entrega estudiantil"}</p><p>Estado: {o.estado.replace(/_/g," ")}</p><p>Total: ${o.total}</p>{siguienteEstado(o.estado,o.metodo_entrega)&&<Boton onClick={()=>void avanzar(o)}>{textoAccion(o.estado)}</Boton>}</article></Tarjeta>)}</div>}</Pantalla>}
