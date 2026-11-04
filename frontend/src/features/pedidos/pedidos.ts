// Lógica de presentación de "Mis pedidos" (sin dinero: el total ya viene calculado del servidor).
export type OrdenResumen = {
  id: number;
  estado: "PAGADA" | "EN_PREPARACION" | "ENVIADA" | "ENTREGADA";
  punto_venta: { id: number; nombre: string };
  metodo_entrega: "pickup" | "estudiante";
  piezas: number;
  total: string;
  creada_en: string | null;
};

export function textoEstado(estado: OrdenResumen["estado"], metodo: OrdenResumen["metodo_entrega"]): string {
  switch (estado) {
    case "PAGADA":
      return "Pagado";
    case "EN_PREPARACION":
      return "En preparación";
    case "ENVIADA":
      return metodo === "pickup" ? "Listo para recoger" : "En camino";
    case "ENTREGADA":
      return "Entregado";
  }
}

export function agrupar(ordenes: OrdenResumen[]) {
  return {
    enCurso: ordenes.filter((o) => o.estado !== "ENTREGADA"),
    anteriores: ordenes.filter((o) => o.estado === "ENTREGADA"),
  };
}

const formato = new Intl.DateTimeFormat("es-MX", { day: "numeric", month: "short", hour: "numeric", minute: "2-digit" });

export function textoFecha(iso: string | null): string {
  return iso ? formato.format(new Date(iso)) : "";
}
