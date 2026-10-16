// Vista 03 · Menú del puesto. Ver docs/diseno/03-menu.png
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, ApiError } from "../../api/client";
import { desdeCentavos, pesos } from "../../api/dinero";
import { Boton, Chip, FilaProducto, Pantalla } from "../../components";
import { IconoAtras } from "../../components/iconos";
import { piezas, subtotalCentavos, useCarrito } from "../carrito/carrito";
import type { PuntoVenta } from "../explorar/ExplorarPage";
import { textoDistancia } from "../explorar/ExplorarPage";
import { useUbicacion } from "../explorar/ubicacion";
import "./menu.css";

type Producto = { id: number; punto_venta_id: number; nombre: string; descripcion: string; precio: string; disponible: boolean };

export function MenuPage() {
  const id = Number(useParams().id);
  const ubicacion = useUbicacion();
  const navegar = useNavigate();
  const { carrito, despachar } = useCarrito();
  const [punto, setPunto] = useState<PuntoVenta | null>(null);
  const [menu, setMenu] = useState<Producto[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const params = new URLSearchParams({ lat: String(ubicacion.lat), lon: String(ubicacion.lon) });
    Promise.all([api<PuntoVenta>(`/puntos-venta/${id}?${params}`), api<Producto[]>(`/puntos-venta/${id}/productos`)])
      .then(([p, m]) => {
        setPunto(p);
        setMenu(m);
      })
      .catch((e) => setError((e as ApiError).message));
  }, [id, ubicacion.lat, ubicacion.lon]);

  if (error) {
    return (
      <Pantalla nav>
        <div className="seccion menu__error">
          <p className="error-campo" role="alert">{error}</p>
          <Link to="/explorar">Volver a explorar</Link>
        </div>
      </Pantalla>
    );
  }
  if (!punto || !menu) return <Pantalla><p className="seccion menu__cargando texto-muted">Cargando menú…</p></Pantalla>;

  const esEstePuesto = carrito.punto?.id === punto.id;
  const cantidad = (productoId: number) =>
    esEstePuesto ? carrito.lineas.find((l) => l.producto_id === productoId)?.cantidad ?? 0 : 0;

  const agregar = (p: Producto) => {
    if (carrito.punto && !esEstePuesto && carrito.lineas.length) {
      const ok = window.confirm(`Tu carrito tiene productos de ${carrito.punto.nombre}. ¿Vaciarlo y empezar uno en ${punto.nombre}?`);
      if (!ok) return;
    }
    despachar({ tipo: "agregar", punto: { id: punto.id, nombre: punto.nombre }, producto: p });
  };

  const barra = esEstePuesto && piezas(carrito) > 0 && (
    <Boton onClick={() => navegar("/carrito")}>
      Ver carrito ({piezas(carrito)}) · {pesos(desdeCentavos(subtotalCentavos(carrito)))}
    </Boton>
  );

  return (
    <Pantalla barra={barra || undefined} nav={!barra}>
      <header className="menu__portada">
        <Link to="/explorar" className="menu__atras">
          <IconoAtras tam={22} /> Explorar
        </Link>
        <h1 className="marca menu__nombre">{punto.nombre}</h1>
        <p className="menu__lugar">
          {punto.ubicacion_texto}
          {punto.distancia_m !== null && ` · ${textoDistancia(punto.distancia_m)}`}
        </p>
        <div className="menu__chips">
          <Chip>★ {punto.calificacion.toFixed(1)} ({punto.num_resenas})</Chip>
          <Chip>{punto.abierto ? `Abierto hasta ${punto.horario_cierre}` : "Cerrado ahora"}</Chip>
          <Chip>{punto.admite_entrega ? "Pickup · Entrega" : "Solo pickup"}</Chip>
        </div>
      </header>

      <section className="seccion">
        <h2 className="titulo-seccion">Menú</h2>
        {!punto.abierto && <p className="menu__aviso">Este puesto está cerrado; puedes ver el menú pero no pedir.</p>}
        {menu.map((p) => (
          <FilaProducto
            key={p.id}
            nombre={p.nombre}
            descripcion={p.disponible ? p.descripcion : "Agotado por hoy"}
            precio={pesos(p.precio)}
            cantidad={cantidad(p.id)}
            deshabilitado={!punto.abierto || !p.disponible}
            onAgregar={() => agregar(p)}
            onQuitar={() => despachar({ tipo: "quitar", producto_id: p.id })}
          />
        ))}
      </section>
    </Pantalla>
  );
}
