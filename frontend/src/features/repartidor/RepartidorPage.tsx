import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "../../api/client";
import { Boton, Pantalla, Tarjeta } from "../../components";
import { useSesion } from "../cuenta/sesion";
import { type EntregaDisponible, textoDistancia, textoEstadoEntrega } from "./repartidor";
import "./repartidor.css";

export function RepartidorPage() {
  const { usuario } = useSesion();
  const [entregas, setEntregas] = useState<EntregaDisponible[]>([]);
  const [cargando, setCargando] = useState(true);
  const [aceptando, setAceptando] = useState<number | null>(null);
  const [error, setError] = useState("");

  const cargar = useCallback(async () => {
    try {
      const respuesta = await api<{ entregas: EntregaDisponible[] }>("/entregas/disponibles");
      setEntregas(respuesta.entregas);
      setError("");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "No se pudieron cargar las entregas.");
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    if (usuario?.rol === "repartidor") void cargar();
  }, [cargar, usuario]);

  async function aceptar(ordenId: number) {
    setAceptando(ordenId);
    setError("");
    try {
      await api(`/entregas/${ordenId}/aceptar`, { method: "POST" });
      await cargar();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "No se pudo aceptar la entrega.");
      if (e instanceof ApiError && e.status === 409) await cargar();
    } finally {
      setAceptando(null);
    }
  }

  if (usuario && usuario.rol !== "repartidor") {
    return <Pantalla nav><div className="repartidor__vacio"><p role="alert">Esta pantalla requiere una cuenta de repartidor.</p></div></Pantalla>;
  }

  return (
    <Pantalla nav>
      <header className="repartidor__encabezado">
        <p>Modo repartidor</p>
        <h1>Entregas disponibles</h1>
      </header>
      {error && <p className="error-campo" role="alert">{error}</p>}
      {cargando ? <p className="repartidor__vacio" role="status">Cargando entregas…</p>
        : entregas.length === 0 ? <p className="repartidor__vacio">No hay entregas disponibles.</p>
        : <div className="repartidor__lista">
          {entregas.map((entrega) => (
            <Tarjeta key={entrega.orden_id} className="repartidor__tarjeta">
              <div className="repartidor__ganancia">Ganancia ${entrega.ganancia}</div>
              <p className="repartidor__dato"><span>Recoger</span><strong>{entrega.puesto}</strong></p>
              <p className="repartidor__dato"><span>Ubicación</span><strong>{entrega.lugar_recogida}</strong></p>
              <p className="repartidor__dato"><span>Entregar</span><strong>{entrega.destino ?? "Destino no disponible"}</strong></p>
              <p className="repartidor__lineas">Pedido #{entrega.orden_id} · {entrega.lineas.map((l) => `${l.cantidad}× ${l.nombre}`).join(" · ")}</p>
              <p className="repartidor__dato"><span>Distancia</span><strong>{textoDistancia(entrega.distancia_km)}</strong></p>
              <p className="repartidor__lineas">Estado: {textoEstadoEntrega(entrega.estado)}</p>
              <Boton className="repartidor__boton" cargando={aceptando === entrega.orden_id}
                disabled={aceptando !== null} onClick={() => void aceptar(entrega.orden_id)}>
                Aceptar entrega
              </Boton>
            </Tarjeta>
          ))}
        </div>}
    </Pantalla>
  );
}
