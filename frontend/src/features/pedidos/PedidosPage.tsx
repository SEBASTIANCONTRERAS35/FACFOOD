// Mis pedidos: historial del usuario; cada pedido abre su seguimiento (vista 05).
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, ApiError } from "../../api/client";
import { pesos } from "../../api/dinero";
import { Pantalla } from "../../components";
import { IconoCubiertos } from "../../components/iconos";
import type { OrdenResumen } from "./pedidos";
import { agrupar, textoEstado, textoFecha } from "./pedidos";
import "./pedidos.css";

export function PedidosPage() {
  const navegar = useNavigate();
  const [ordenes, setOrdenes] = useState<OrdenResumen[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<OrdenResumen[]>("/usuarios/me/ordenes").then(setOrdenes).catch((e) => setError((e as ApiError).message));
  }, []);

  const tarjeta = (o: OrdenResumen) => (
    <button key={o.id} type="button" className="pedido" onClick={() => navegar(`/pedido/${o.id}`)}>
      <span className="pedido__icono" aria-hidden="true">
        <IconoCubiertos tam={24} />
      </span>
      <span className="pedido__info">
        <span className="pedido__puesto">{o.punto_venta.nombre}</span>
        <span className="pedido__detalle">
          Pedido #{o.id} · {o.piezas} {o.piezas === 1 ? "producto" : "productos"} ·{" "}
          {o.metodo_entrega === "pickup" ? "Pickup" : "Entrega"}
        </span>
        <span className="pedido__detalle">{textoFecha(o.creada_en)}</span>
      </span>
      <span className="pedido__lado">
        <span className={`pedido__estado pedido__estado--${o.estado.toLowerCase()}`}>
          {textoEstado(o.estado, o.metodo_entrega)}
        </span>
        <span className="pedido__total">{pesos(o.total)}</span>
      </span>
    </button>
  );

  const { enCurso, anteriores } = agrupar(ordenes ?? []);

  return (
    <Pantalla nav>
      <div className="seccion pedidos">
        <h1 className="pedidos__titulo">Mis pedidos</h1>
        {error && <p className="error-campo" role="alert">{error}</p>}
        {!error && ordenes === null && <p className="texto-muted">Cargando tus pedidos…</p>}
        {ordenes?.length === 0 && (
          <div className="pedidos__vacio">
            <p>Aún no tienes pedidos.</p>
            <Link to="/explorar" className="boton boton--primario pedidos__enlace">Explorar puestos</Link>
          </div>
        )}
        {enCurso.length > 0 && (
          <section aria-label="Pedidos en curso">
            <h2 className="titulo-seccion">En curso</h2>
            <div className="pedidos__lista">{enCurso.map(tarjeta)}</div>
          </section>
        )}
        {anteriores.length > 0 && (
          <section aria-label="Pedidos anteriores">
            <h2 className="titulo-seccion">Anteriores</h2>
            <div className="pedidos__lista">{anteriores.map(tarjeta)}</div>
          </section>
        )}
      </div>
    </Pantalla>
  );
}
