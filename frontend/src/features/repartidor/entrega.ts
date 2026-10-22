export type EstadoOrdenEntrega = "PAGADA" | "EN_PREPARACION" | "ENVIADA" | "ENTREGADA";
export type EstadoAsignacion = "ACEPTADA" | "RECOGIDA" | "ENTREGADA";

export type EntregaDetalle = {
  orden_id: number;
  estado_orden: EstadoOrdenEntrega;
  estado_entrega: EstadoAsignacion;
  puesto: { nombre: string; ubicacion: string; lat: number; lon: number };
  destino: { nombre: string; lat: number; lon: number } | null;
  lineas: { nombre: string; cantidad: number }[];
  distancia_km: string;
  ganancia: string;
  aceptada_en: string | null;
  recogida_en: string | null;
  entregada_en: string | null;
};

export function puedeRecoger(entrega: EntregaDetalle): boolean {
  return entrega.estado_entrega === "ACEPTADA" && entrega.estado_orden === "EN_PREPARACION";
}

export function puedeEntregar(entrega: EntregaDetalle): boolean {
  return entrega.estado_entrega === "RECOGIDA" && entrega.estado_orden === "ENVIADA";
}

export function codigoValido(codigo: string): boolean {
  return /^[0-9]{4}$/.test(codigo);
}

export function etiquetaEstadoOrden(estado: EstadoOrdenEntrega): string {
  return ({
    PAGADA: "Pagada",
    EN_PREPARACION: "En preparación",
    ENVIADA: "En camino",
    ENTREGADA: "Entregada",
  })[estado];
}

export function etiquetaEstadoEntrega(estado: EstadoAsignacion): string {
  return ({
    ACEPTADA: "Aceptada",
    RECOGIDA: "Recogida",
    ENTREGADA: "Entregada",
  })[estado];
}
