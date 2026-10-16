// Carrito: en memoria y en localStorage, de un solo puesto a la vez.
// Los montos que se muestran aquí son una estimación; el total real lo calcula el servidor al crear la orden.
import type { ReactNode } from "react";
import { createContext, useContext, useEffect, useReducer } from "react";
import { aCentavos } from "../../api/dinero";

export type LineaCarrito = { producto_id: number; nombre: string; precio: string; cantidad: number };
export type EstadoCarrito = { punto: { id: number; nombre: string } | null; lineas: LineaCarrito[]; ordenId: number | null };

export type Accion =
  | { tipo: "agregar"; punto: { id: number; nombre: string }; producto: { id: number; nombre: string; precio: string } }
  | { tipo: "quitar"; producto_id: number }
  | { tipo: "vaciar" }
  | { tipo: "orden"; id: number | null };

export const VACIO: EstadoCarrito = { punto: null, lineas: [], ordenId: null };

export function reducir(estado: EstadoCarrito, accion: Accion): EstadoCarrito {
  switch (accion.tipo) {
    case "agregar": {
      const base = estado.punto && estado.punto.id !== accion.punto.id ? VACIO : estado;
      const existe = base.lineas.find((l) => l.producto_id === accion.producto.id);
      const lineas = existe
        ? base.lineas.map((l) => (l.producto_id === accion.producto.id ? { ...l, cantidad: l.cantidad + 1 } : l))
        : [...base.lineas, { producto_id: accion.producto.id, nombre: accion.producto.nombre, precio: accion.producto.precio, cantidad: 1 }];
      // Cambió el contenido: la orden que se hubiera creado ya no corresponde.
      return { punto: accion.punto, lineas, ordenId: null };
    }
    case "quitar": {
      const lineas = estado.lineas
        .map((l) => (l.producto_id === accion.producto_id ? { ...l, cantidad: l.cantidad - 1 } : l))
        .filter((l) => l.cantidad > 0);
      return lineas.length ? { ...estado, lineas, ordenId: null } : VACIO;
    }
    case "vaciar":
      return VACIO;
    case "orden":
      return { ...estado, ordenId: accion.id };
  }
}

export const piezas = (e: EstadoCarrito) => e.lineas.reduce((n, l) => n + l.cantidad, 0);
export const subtotalCentavos = (e: EstadoCarrito) =>
  e.lineas.reduce((t, l) => t + aCentavos(l.precio) * l.cantidad, 0);

const CLAVE = "facfood.carrito";

function inicial(): EstadoCarrito {
  try {
    return { ...VACIO, ...JSON.parse(localStorage.getItem(CLAVE) ?? "null") };
  } catch {
    return VACIO;
  }
}

type ContextoCarrito = { carrito: EstadoCarrito; despachar: (a: Accion) => void };
const Contexto = createContext<ContextoCarrito | null>(null);

export function ProveedorCarrito({ children }: { children: ReactNode }) {
  const [carrito, despachar] = useReducer(reducir, undefined, inicial);
  useEffect(() => localStorage.setItem(CLAVE, JSON.stringify(carrito)), [carrito]);
  return <Contexto.Provider value={{ carrito, despachar }}>{children}</Contexto.Provider>;
}

export function useCarrito() {
  const c = useContext(Contexto);
  if (!c) throw new Error("useCarrito debe usarse dentro de <ProveedorCarrito>");
  return c;
}
