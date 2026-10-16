// Objeto Orden de la API (docs/CONTRATO.md §6). El dinero es texto con 2 decimales.
export type Orden = {
  id: number;
  estado: "CREADA" | "PAGADA" | "EN_PREPARACION" | "ENVIADA" | "ENTREGADA" | "CANCELADA";
  comprador_id: number;
  punto_venta: { id: number; nombre: string };
  lineas: { producto_id: number; nombre: string; cantidad: number; precio_unitario: string; importe: string }[];
  metodo_entrega: "pickup" | "estudiante";
  destino: { id: number; nombre: string } | null;
  distancia_km: string;
  subtotal: string;
  descuento: string;
  origen_descuento: "cupon" | "lealtad" | null;
  cupon: string | null;
  iva: string;
  envio: string;
  total: string;
  codigo_entrega: string | null;
  factura_folio: string | null;
  creada_en: string | null;
};
