// Lógica de presentación de la vista Cupones (los montos ya vienen como texto del servidor).
import { pesos } from "../../api/dinero";

export type Lealtad = {
  nivel: "bronce" | "plata" | "oro";
  descuento_pct: number;
  pedidos_completados: number;
  siguiente: { nivel: "plata" | "oro"; pedidos: number; faltan: number; descuento_pct: number } | null;
};

export type Cupon = {
  codigo: string;
  porcentaje: number;
  pedido_minimo: string;
  tope_descuento: string | null;
  vigente_hasta: string; // AAAA-MM-DD
  solo_primer_pedido: boolean;
  uno_por_usuario: boolean;
  estado: "disponible" | "usado";
};

export const NOMBRE_NIVEL = { bronce: "Bronce", plata: "Plata", oro: "Oro" } as const;

/** Avance hacia el siguiente nivel, de 0 a 1 (1 si ya es oro). */
export function progreso(l: Lealtad): number {
  if (!l.siguiente) return 1;
  return Math.min(1, l.pedidos_completados / l.siguiente.pedidos);
}

const fecha = new Intl.DateTimeFormat("es-MX", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });

export function condiciones(c: Cupon): string[] {
  const partes: string[] = [];
  if (c.tope_descuento) partes.push(`Hasta ${pesos(c.tope_descuento)} de descuento`);
  if (c.pedido_minimo !== "0.00") partes.push(`Pedido mínimo ${pesos(c.pedido_minimo)}`);
  if (c.solo_primer_pedido) partes.push("Solo tu primer pedido");
  else if (c.uno_por_usuario) partes.push("Una vez por persona");
  partes.push(`Vigente hasta el ${fecha.format(new Date(c.vigente_hasta + "T00:00:00Z"))}`);
  return partes;
}
