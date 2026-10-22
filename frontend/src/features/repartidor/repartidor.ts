export type EntregaDisponible = {
  orden_id: number;
  estado: "PAGADA" | "EN_PREPARACION";
  puesto: string;
  lugar_recogida: string;
  destino: string | null;
  lineas: { nombre: string; cantidad: number }[];
  distancia_km: string;
  ganancia: string;
};

export function textoEstadoEntrega(estado: EntregaDisponible["estado"]): string {
  return estado === "PAGADA" ? "Pagado" : "En preparación";
}

export function textoDistancia(distancia: string): string {
  return `${distancia} km`;
}
