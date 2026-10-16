// Vista 04 · Carrito y pago. Ver docs/diseno/04-carrito-pago.png
// Todos los montos que se muestran vienen del servidor: aquí no se calcula dinero.
import type { FormEvent } from "react";
import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, ApiError } from "../../api/client";
import { pesos } from "../../api/dinero";
import { Boton, Campo, Pantalla, Tarjeta } from "../../components";
import { IconoAtras, IconoEstrella } from "../../components/iconos";
import { useSesion } from "../cuenta/sesion";
import type { PuntoVenta } from "../explorar/ExplorarPage";
import { useCarrito } from "./carrito";
import type { Orden } from "./tipos";
import "./carrito.css";

type Destino = { id: number; nombre: string };
const NIVEL = { bronce: "Bronce", plata: "Plata", oro: "Oro" };

export function CarritoPage() {
  const { carrito, despachar } = useCarrito();
  const { usuario } = useSesion();
  const navegar = useNavigate();
  const [orden, setOrden] = useState<Orden | null>(null);
  const [punto, setPunto] = useState<PuntoVenta | null>(null);
  const [destinos, setDestinos] = useState<Destino[]>([]);
  const [codigo, setCodigo] = useState("");
  const [rfc, setRfc] = useState("");
  const [pedirRfc, setPedirRfc] = useState(false);
  const [error, setError] = useState("");
  const [errorCupon, setErrorCupon] = useState("");
  const [ocupado, setOcupado] = useState(false);
  const iniciado = useRef(false);

  // Crea la orden (o reutiliza la del carrito) al entrar.
  useEffect(() => {
    if (iniciado.current || !carrito.punto || !carrito.lineas.length) return;
    iniciado.current = true;
    const crear = () =>
      api<Orden>("/ordenes", {
        method: "POST",
        body: {
          punto_venta_id: carrito.punto!.id,
          lineas: carrito.lineas.map((l) => ({ producto_id: l.producto_id, cantidad: l.cantidad })),
          metodo_entrega: "pickup",
        },
      });
    const existente = carrito.ordenId
      ? api<Orden>(`/ordenes/${carrito.ordenId}/entrega`, { method: "PATCH", body: { metodo_entrega: "pickup" } }).catch(crear)
      : crear();
    existente
      .then((o) => {
        setOrden(o);
        despachar({ tipo: "orden", id: o.id });
      })
      .catch((e) => setError((e as ApiError).message));
    api<PuntoVenta>(`/puntos-venta/${carrito.punto.id}`).then(setPunto).catch(() => setPunto(null));
    api<Destino[]>("/destinos").then(setDestinos).catch(() => setDestinos([]));
  }, [carrito, despachar]);

  async function accion(promesa: Promise<Orden>, alFallar: (m: string) => void = setError) {
    setOcupado(true);
    alFallar("");
    try {
      setOrden(await promesa);
      return true;
    } catch (e) {
      alFallar((e as ApiError).message);
      return false;
    } finally {
      setOcupado(false);
    }
  }

  const cambiarEntrega = (metodo: "pickup" | "estudiante", destinoId?: number) => {
    if (!orden) return;
    if (metodo === "estudiante" && !destinoId) {
      // Se elige primero el destino; mientras, se marca la opción sin llamar a la API.
      setOrden({ ...orden, metodo_entrega: "estudiante", destino: null });
      return;
    }
    accion(api<Orden>(`/ordenes/${orden.id}/entrega`, {
      method: "PATCH", body: { metodo_entrega: metodo, destino_id: destinoId ?? null },
    }));
  };

  const aplicarCupon = (e: FormEvent) => {
    e.preventDefault();
    if (!orden || !codigo.trim()) return;
    accion(api<Orden>(`/ordenes/${orden.id}/cupon`, { method: "POST", body: { codigo: codigo.trim() } }), setErrorCupon)
      .then((ok) => ok && setCodigo(""));
  };

  const quitarCupon = () => orden && accion(api<Orden>(`/ordenes/${orden.id}/cupon`, { method: "DELETE" }), setErrorCupon);

  async function pagar() {
    if (!orden) return;
    setOcupado(true);
    setError("");
    try {
      const pagada = await api<Orden>(`/ordenes/${orden.id}/pagar`, { method: "POST", body: { rfc: pedirRfc && rfc.trim() ? rfc.trim() : null } });
      despachar({ tipo: "vaciar" });
      navegar(`/pedido/${pagada.id}`, { replace: true });
    } catch (e) {
      setError((e as ApiError).message);
      setOcupado(false);
    }
  }

  if (!carrito.lineas.length && !orden) {
    return (
      <Pantalla nav>
        <div className="seccion carrito__vacio">
          <h1>Tu carrito está vacío</h1>
          <p className="texto-muted">Elige un puesto y agrega lo que se te antoje.</p>
          <Link to="/explorar" className="boton boton--primario carrito__enlace">Explorar puestos</Link>
        </div>
      </Pantalla>
    );
  }

  const esperandoDestino = orden?.metodo_entrega === "estudiante" && !orden.destino;
  const barra = orden && (
    <>
      <Boton onClick={pagar} cargando={ocupado} disabled={esperandoDestino}>
        {esperandoDestino ? "Elige a dónde te lo llevamos" : `Pagar ${pesos(orden.total)}`}
      </Boton>
      <p className="carrito__nota">Pago simulado en el MVP · Recibirás tu factura al pagar</p>
    </>
  );

  return (
    <Pantalla barra={barra || undefined}>
      <header className="carrito__encabezado">
        <Link to={carrito.punto ? `/puesto/${carrito.punto.id}` : "/explorar"} aria-label="Volver al menú">
          <IconoAtras tam={22} />
        </Link>
        <h1>Tu pedido · {orden?.punto_venta.nombre ?? carrito.punto?.nombre}</h1>
      </header>

      <div className="seccion carrito">
        {error && <p className="error-campo" role="alert">{error}</p>}
        {!orden && !error && <p className="texto-muted">Preparando tu orden…</p>}

        {orden && (
          <>
            <Tarjeta>
              {orden.lineas.map((l) => (
                <div key={l.producto_id} className="carrito__linea">
                  <span className="carrito__cantidad">{l.cantidad}×</span>
                  <span className="carrito__producto">{l.nombre}</span>
                  <span>{pesos(l.importe)}</span>
                </div>
              ))}
            </Tarjeta>

            <h2 className="carrito__subtitulo">¿Cómo lo recibes?</h2>
            <div className="carrito__opciones" role="radiogroup" aria-label="Método de entrega">
              <button type="button" role="radio" aria-checked={orden.metodo_entrega === "pickup"}
                className="opcion" onClick={() => cambiarEntrega("pickup")} disabled={ocupado}>
                <strong>Pickup</strong>
                <span>Lo recoges · Gratis</span>
              </button>
              <button type="button" role="radio" aria-checked={orden.metodo_entrega === "estudiante"}
                className="opcion" onClick={() => cambiarEntrega("estudiante", orden.destino?.id)}
                disabled={ocupado || punto?.admite_entrega === false}>
                <strong>Entrega estudiante</strong>
                <span>
                  {punto?.admite_entrega === false
                    ? "Este puesto no ofrece entrega"
                    : orden.metodo_entrega === "estudiante" && orden.destino
                      ? `+${pesos(orden.envio)} · ${Math.round(Number(orden.distancia_km) * 1000)} m ($5/km)`
                      : "$5 por km"}
                </span>
              </button>
            </div>
            {orden.metodo_entrega === "estudiante" && (
              <label className="carrito__destino">
                <span className="solo-lectores">¿A dónde te lo llevamos?</span>
                <select value={orden.destino?.id ?? ""} disabled={ocupado}
                  onChange={(e) => cambiarEntrega("estudiante", Number(e.target.value))}>
                  <option value="" disabled>¿A dónde te lo llevamos?</option>
                  {destinos.map((d) => <option key={d.id} value={d.id}>{d.nombre}</option>)}
                </select>
              </label>
            )}

            {orden.cupon ? (
              <div className="carrito__cupon-aplicado">
                <span>Cupón <strong>{orden.cupon}</strong></span>
                <button type="button" onClick={quitarCupon} disabled={ocupado}>Quitar</button>
              </div>
            ) : (
              <form className="carrito__cupon" onSubmit={aplicarCupon}>
                <Campo id="cupon" placeholder="Código de cupón" value={codigo} autoCapitalize="characters"
                  onChange={(e) => { setCodigo(e.target.value); setErrorCupon(""); }} />
                <Boton type="submit" variante="secundario" disabled={!codigo.trim() || ocupado}>Aplicar</Boton>
              </form>
            )}
            {errorCupon && <p className="error-campo" role="alert">{errorCupon}</p>}

            {orden.origen_descuento && (
              <div className="carrito__aviso" role="status">
                <IconoEstrella tam={20} />
                <span>
                  {orden.origen_descuento === "cupon"
                    ? `Cupón ${orden.cupon} aplicado: −${pesos(orden.descuento)}.`
                    : `Tu nivel ${usuario ? NIVEL[usuario.nivel_lealtad] : ""} te da −${pesos(orden.descuento)}.`}{" "}
                  Los descuentos no se acumulan: se usa el mayor entre cupón y lealtad.
                </span>
              </div>
            )}

            <Tarjeta className="carrito__resumen">
              <Fila k="Subtotal" v={pesos(orden.subtotal)} />
              {orden.origen_descuento && (
                <Fila
                  k={orden.origen_descuento === "cupon" ? `Descuento (${orden.cupon})` : "Descuento (lealtad)"}
                  v={`−${pesos(orden.descuento)}`}
                  verde
                />
              )}
              <Fila k="IVA 16%" v={pesos(orden.iva)} />
              <Fila k={orden.metodo_entrega === "pickup" ? "Envío (Pickup)" : "Envío (Entrega estudiante)"} v={pesos(orden.envio)} />
              <hr />
              <Fila k="Total" v={pesos(orden.total)} total />
            </Tarjeta>

            {pedirRfc ? (
              <Campo id="rfc" placeholder="RFC para la factura (opcional)" value={rfc} maxLength={13}
                autoCapitalize="characters" onChange={(e) => setRfc(e.target.value)} />
            ) : (
              <button type="button" className="carrito__rfc" onClick={() => setPedirRfc(true)}>
                ¿Necesitas factura a tu RFC?
              </button>
            )}
          </>
        )}
      </div>
    </Pantalla>
  );
}

function Fila({ k, v, verde, total }: { k: string; v: string; verde?: boolean; total?: boolean }) {
  return (
    <div className={`carrito__fila ${total ? "carrito__fila--total" : ""}`}>
      <span>{k}</span>
      <span className={verde ? "carrito__verde" : undefined}>{v}</span>
    </div>
  );
}
