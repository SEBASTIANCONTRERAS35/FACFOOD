import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, ApiError } from "../../api/client";
import { pesos } from "../../api/dinero";
import { Boton, Campo, Pantalla, Tarjeta } from "../../components";
import { Mapa } from "../../components/Mapa";
import { useSesion } from "../cuenta/sesion";
import {
  codigoValido,
  etiquetaEstadoEntrega,
  etiquetaEstadoOrden,
  puedeEntregar,
  puedeRecoger,
  type EntregaDetalle,
} from "./entrega";
import "./repartidor.css";
import "./entrega.css";

export function EntregaPage() {
  const { id: idTexto } = useParams();
  const ordenId = Number(idTexto);
  const { usuario } = useSesion();
  const [entrega, setEntrega] = useState<EntregaDetalle | null>(null);
  const [cargando, setCargando] = useState(true);
  const [accionando, setAccionando] = useState(false);
  const [codigo, setCodigo] = useState("");
  const [error, setError] = useState("");

  const cargar = useCallback(async (signal?: AbortSignal) => {
    if (!Number.isSafeInteger(ordenId) || ordenId < 1) {
      setEntrega(null);
      setError("La entrega no existe.");
      setCargando(false);
      return;
    }
    if (usuario?.rol !== "repartidor") return;
    setCargando(true);
    try {
      const resultado = await api<EntregaDetalle>(`/entregas/${ordenId}`, { signal });
      setEntrega(resultado);
      setError("");
    } catch (e) {
      if ((e as Error).name !== "AbortError") {
        setEntrega(null);
        setError(e instanceof ApiError ? e.message : "No se pudo cargar la entrega.");
      }
    } finally {
      if (!signal?.aborted) setCargando(false);
    }
  }, [ordenId, usuario]);

  useEffect(() => {
    const controller = new AbortController();
    void cargar(controller.signal);
    return () => controller.abort();
  }, [cargar]);

  async function ejecutar(accion: "recoger" | "entregar") {
    setAccionando(true);
    setError("");
    try {
      const resultado = await api<EntregaDetalle>(`/entregas/${ordenId}/${accion}`, {
        method: "POST",
        ...(accion === "entregar" ? { body: { codigo_entrega: codigo } } : {}),
      });
      setEntrega(resultado);
      setCodigo("");
    } catch (e) {
      const mensaje = e instanceof ApiError ? e.message : "No se pudo actualizar la entrega.";
      if (e instanceof ApiError && [403, 404, 409].includes(e.status)) await cargar();
      setError(mensaje);
    } finally {
      setAccionando(false);
    }
  }

  if (usuario && usuario.rol !== "repartidor") {
    return <Pantalla nav><div className="repartidor__vacio"><p role="alert">Esta pantalla requiere una cuenta de repartidor.</p></div></Pantalla>;
  }

  if (cargando) {
    return <Pantalla nav><p className="repartidor__vacio" role="status">Cargando entrega…</p></Pantalla>;
  }

  if (!entrega) {
    return <Pantalla nav><div className="repartidor__vacio"><h1>Entrega no disponible</h1><p role="alert">{error}</p></div></Pantalla>;
  }

  const puedeConfirmar = puedeEntregar(entrega) && codigoValido(codigo) && !accionando;
  const barra = puedeRecoger(entrega)
    ? <Boton className="repartidor__boton" cargando={accionando} onClick={() => void ejecutar("recoger")}>Marcar como recogido</Boton>
    : puedeEntregar(entrega)
      ? <Boton className="repartidor__boton" cargando={accionando} disabled={!puedeConfirmar}
          onClick={() => void ejecutar("entregar")}>Marcar como entregado</Boton>
      : undefined;

  return (
    <Pantalla nav barra={barra}>
      <header className="entrega__encabezado">
        <h1>Pedido #{entrega.orden_id}</h1>
        <p>{entrega.puesto.nombre} · Ganancia {pesos(entrega.ganancia)}</p>
      </header>
      {entrega.destino && (
        <Tarjeta className="entrega__mapa">
          <Mapa
            centro={{ lat: (entrega.puesto.lat + entrega.destino.lat) / 2, lon: (entrega.puesto.lon + entrega.destino.lon) / 2 }}
            zoom={15}
            alto={220}
            pines={[
              { id: "puesto", lat: entrega.puesto.lat, lon: entrega.puesto.lon, etiqueta: entrega.puesto.nombre, color: "dorado" },
              { id: "destino", lat: entrega.destino.lat, lon: entrega.destino.lon, etiqueta: entrega.destino.nombre, color: "marino" },
            ]}
          />
        </Tarjeta>
      )}
      <div className="repartidor__lista">
        <Tarjeta className="entrega__datos">
          <p><strong>Recoger en</strong><br />{entrega.puesto.nombre} · {entrega.puesto.ubicacion}</p>
          <p><strong>Entregar en</strong><br />{entrega.destino?.nombre ?? "Destino no disponible"}</p>
          <p>Distancia: {entrega.distancia_km} km</p>
          <p>Pedido #{entrega.orden_id} · {entrega.lineas.map((l) => `${l.cantidad}× ${l.nombre}`).join(" · ")}</p>
        </Tarjeta>
        <Tarjeta className="entrega__estados">
          <p><strong>Estado de la orden:</strong> {etiquetaEstadoOrden(entrega.estado_orden)}</p>
          <p><strong>Estado de la entrega:</strong> {etiquetaEstadoEntrega(entrega.estado_entrega)}</p>
          {entrega.aceptada_en && <p>Asignada: {new Date(entrega.aceptada_en).toLocaleString("es-MX")}</p>}
          {entrega.recogida_en && <p>Recogida: {new Date(entrega.recogida_en).toLocaleString("es-MX")}</p>}
          {entrega.entregada_en && <p>Entregada: {new Date(entrega.entregada_en).toLocaleString("es-MX")}</p>}
        </Tarjeta>
        {entrega.estado_orden === "PAGADA" && entrega.estado_entrega === "ACEPTADA" &&
          <p className="texto-muted">El puesto aún prepara el pedido; podrás recogerlo cuando esté listo.</p>}
        {puedeEntregar(entrega) && (
          <Tarjeta className="entrega__codigo">
            <p>Al llegar, pide al cliente su código de entrega de cuatro dígitos.</p>
            <Campo id="codigo_entrega" placeholder="Código de entrega" type="text" inputMode="numeric"
              autoComplete="one-time-code" maxLength={4} pattern="[0-9]{4}" value={codigo}
              onChange={(e) => setCodigo(e.target.value)} disabled={accionando} />
            {codigo.length > 0 && !codigoValido(codigo) &&
              <p className="error-campo" role="alert">Escribe exactamente cuatro dígitos.</p>}
            {error && <p className="error-campo" role="alert">{error}</p>}
          </Tarjeta>
        )}
      </div>
      {error && !puedeEntregar(entrega) && <p className="error-campo" role="alert">{error}</p>}
    </Pantalla>
  );
}
