// Cupones: nivel de lealtad y cupones que el usuario puede usar (filtrados por el servidor).
import { useEffect, useState } from "react";
import { api, ApiError } from "../../api/client";
import { Pantalla } from "../../components";
import { IconoCupon, IconoEstrella } from "../../components/iconos";
import type { Cupon, Lealtad } from "./cupones";
import { condiciones, NOMBRE_NIVEL, progreso } from "./cupones";
import "./cupones.css";

type Respuesta = { lealtad: Lealtad; cupones: Cupon[] };

export function CuponesPage() {
  const [datos, setDatos] = useState<Respuesta | null>(null);
  const [error, setError] = useState("");
  const [copiado, setCopiado] = useState<string | null>(null);

  useEffect(() => {
    api<Respuesta>("/cupones").then(setDatos).catch((e) => setError((e as ApiError).message));
  }, []);

  async function copiar(codigo: string) {
    try {
      await navigator.clipboard.writeText(codigo);
      setCopiado(codigo);
      setTimeout(() => setCopiado(null), 2000);
    } catch {
      setCopiado(null);
    }
  }

  const l = datos?.lealtad;

  return (
    <Pantalla nav>
      <div className="seccion cupones">
        <h1 className="cupones__titulo">Cupones</h1>
        {error && <p className="error-campo" role="alert">{error}</p>}
        {!error && !datos && <p className="texto-muted">Cargando tus cupones…</p>}

        {l && (
          <section className="nivel" aria-label="Tu nivel de lealtad">
            <div className="nivel__fila">
              <IconoEstrella tam={22} />
              <span className="nivel__nombre">Nivel {NOMBRE_NIVEL[l.nivel]}</span>
              <span className="nivel__pct">{l.descuento_pct}% en cada pedido</span>
            </div>
            <div className="nivel__barra" role="progressbar" aria-valuemin={0} aria-valuemax={100}
              aria-valuenow={Math.round(progreso(l) * 100)}>
              <span style={{ width: `${progreso(l) * 100}%` }} />
            </div>
            <p className="nivel__texto">
              {l.siguiente
                ? `Te ${l.siguiente.faltan === 1 ? "falta 1 pedido" : `faltan ${l.siguiente.faltan} pedidos`} para ${NOMBRE_NIVEL[l.siguiente.nivel]} (${l.siguiente.descuento_pct}%).`
                : "Tienes el nivel más alto."}{" "}
              Llevas {l.pedidos_completados} {l.pedidos_completados === 1 ? "pedido completado" : "pedidos completados"}.
            </p>
          </section>
        )}

        {datos && (
          <section aria-label="Cupones disponibles">
            <h2 className="titulo-seccion">Tus cupones</h2>
            {datos.cupones.length === 0 && <p className="texto-muted">Por ahora no tienes cupones disponibles.</p>}
            <div className="cupones__lista">
              {datos.cupones.map((c) => (
                <article key={c.codigo} className={`cupon ${c.estado === "usado" ? "cupon--usado" : ""}`}>
                  <div className="cupon__pct">
                    <span>{c.porcentaje}%</span>
                    <IconoCupon tam={20} />
                  </div>
                  <div className="cupon__info">
                    <span className="cupon__codigo">{c.codigo}</span>
                    <span className="cupon__condiciones">{condiciones(c).join(" · ")}</span>
                  </div>
                  {c.estado === "usado" ? (
                    <span className="cupon__usado">Ya lo usaste</span>
                  ) : (
                    <button type="button" className="cupon__copiar" onClick={() => copiar(c.codigo)}>
                      {copiado === c.codigo ? "¡Copiado!" : "Copiar"}
                    </button>
                  )}
                </article>
              ))}
            </div>
            <p className="cupones__nota">
              Los descuentos no se acumulan: en el carrito se aplica el mayor entre tu cupón y tu nivel.
            </p>
          </section>
        )}
      </div>
    </Pantalla>
  );
}
