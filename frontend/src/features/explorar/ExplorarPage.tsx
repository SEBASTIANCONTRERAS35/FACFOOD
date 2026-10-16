// Vista 02 · Explorar puestos (mapa). Ver docs/diseno/02-explorar.png
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "../../api/client";
import { Chip, Pantalla, TarjetaPuesto } from "../../components";
import { IconoBuscar, IconoUbicacion } from "../../components/iconos";
import { Mapa } from "../../components/Mapa";
import { useUbicacion } from "./ubicacion";
import "./explorar.css";

export type PuntoVenta = {
  id: number;
  nombre: string;
  categoria: string;
  descripcion: string;
  ubicacion_texto: string;
  lat: number;
  lon: number;
  distancia_m: number | null;
  calificacion: number;
  num_resenas: number;
  horario_cierre: string;
  abierto: boolean;
  admite_entrega: boolean;
};

export function textoDistancia(m: number | null) {
  if (m === null) return "";
  return m < 1000 ? `${m} m` : `${(m / 1000).toFixed(1)} km`;
}

function useEspera<T>(valor: T, ms: number) {
  const [listo, setListo] = useState(valor);
  useEffect(() => {
    const t = setTimeout(() => setListo(valor), ms);
    return () => clearTimeout(t);
  }, [valor, ms]);
  return listo;
}

export function ExplorarPage() {
  const ubicacion = useUbicacion();
  const navegar = useNavigate();
  const [categorias, setCategorias] = useState<string[]>([]);
  const [categoria, setCategoria] = useState<string | null>(null);
  const [texto, setTexto] = useState("");
  const busqueda = useEspera(texto.trim(), 300);
  const [puestos, setPuestos] = useState<PuntoVenta[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<string[]>("/puntos-venta/categorias").then(setCategorias).catch(() => setCategorias([]));
  }, []);

  useEffect(() => {
    const control = new AbortController();
    const params = new URLSearchParams({ lat: String(ubicacion.lat), lon: String(ubicacion.lon), radio: "1500" });
    if (categoria) params.set("categoria", categoria);
    if (busqueda) params.set("q", busqueda);
    setError("");
    api<PuntoVenta[]>(`/puntos-venta?${params}`, { signal: control.signal })
      .then(setPuestos)
      .catch((e) => {
        if ((e as Error).name !== "AbortError") setError((e as ApiError).message);
      });
    return () => control.abort();
  }, [ubicacion.lat, ubicacion.lon, categoria, busqueda]);

  const pines = useMemo(
    () => (puestos ?? []).map((p) => ({ id: p.id, lat: p.lat, lon: p.lon, etiqueta: p.nombre })),
    [puestos],
  );

  return (
    <Pantalla nav>
      <header className="explorar__encabezado">
        <p className="explorar__ubicacion">
          <IconoUbicacion tam={18} />
          {ubicacion.real ? "Cerca de ti, CU" : "Facultad de Ingeniería, CU"}
        </p>
        <h1 className="explorar__titulo">¿Qué se te antoja hoy?</h1>
        <label className="campo">
          <IconoBuscar tam={20} />
          <span className="solo-lectores">Buscar</span>
          <input
            type="search"
            placeholder="Buscar tacos, café, chilaquiles…"
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
          />
        </label>
      </header>

      <Mapa centro={ubicacion} yo={ubicacion} pines={pines} alto={280} onPin={(id) => navegar(`/puesto/${id}`)} />

      <div className="explorar__filtros" role="group" aria-label="Filtrar por categoría">
        <Chip activo={categoria === null} onClick={() => setCategoria(null)}>Cerca de mí</Chip>
        {categorias.map((c) => (
          <Chip key={c} activo={categoria === c} onClick={() => setCategoria(categoria === c ? null : c)}>
            {c}
          </Chip>
        ))}
      </div>

      <section className="seccion explorar__lista" aria-live="polite">
        <h2 className="titulo-seccion">Puestos cercanos</h2>
        {error && <p className="error-campo" role="alert">{error}</p>}
        {!error && puestos === null && <p className="texto-muted">Buscando puestos…</p>}
        {!error && puestos?.length === 0 && (
          <p className="texto-muted">No encontramos puestos con ese filtro. Prueba con otra categoría.</p>
        )}
        {puestos?.map((p) => (
          <TarjetaPuesto
            key={p.id}
            nombre={p.nombre}
            detalle={`${p.categoria} · ${textoDistancia(p.distancia_m)} · ★ ${p.calificacion.toFixed(1)}`}
            entrega={p.admite_entrega ? "Pickup · Entrega" : "Pickup"}
            cerrado={!p.abierto}
            onClick={() => navegar(`/puesto/${p.id}`)}
          />
        ))}
      </section>
    </Pantalla>
  );
}
