import { describe, expect, it } from "vitest";
import paginaSource from "./EntregaPage.tsx?raw";
import {
  codigoValido,
  etiquetaEstadoEntrega,
  etiquetaEstadoOrden,
  puedeEntregar,
  puedeRecoger,
  type EntregaDetalle,
} from "./entrega";

const base: EntregaDetalle = {
  orden_id: 1,
  estado_orden: "EN_PREPARACION",
  estado_entrega: "ACEPTADA",
  puesto: { nombre: "Puesto", ubicacion: "Zona conocida", lat: 19, lon: -99 },
  destino: { nombre: "Destino", lat: 19.1, lon: -99.1 },
  lineas: [],
  distancia_km: "0.60",
  ganancia: "3.00",
  aceptada_en: null,
  recogida_en: null,
  entregada_en: null,
};

describe("acciones de entrega en curso", () => {
  it("permite recoger solo si la orden está en preparación y la asignación aceptada", () => {
    expect(puedeRecoger(base)).toBe(true);
    expect(puedeRecoger({ ...base, estado_orden: "PAGADA" })).toBe(false);
    expect(puedeRecoger({ ...base, estado_entrega: "RECOGIDA", estado_orden: "ENVIADA" })).toBe(false);
  });

  it("permite entregar solo después de recoger", () => {
    expect(puedeEntregar({ ...base, estado_orden: "ENVIADA", estado_entrega: "RECOGIDA" })).toBe(true);
    expect(puedeEntregar(base)).toBe(false);
  });

  it("valida cuatro dígitos ASCII y conserva ceros iniciales", () => {
    expect(codigoValido("0042")).toBe(true);
    expect(codigoValido("123")).toBe(false);
    expect(codigoValido("12A4")).toBe(false);
    expect(codigoValido("１２３４")).toBe(false);
  });

  it("presenta los estados sin inventar progreso o estimaciones", () => {
    expect(etiquetaEstadoOrden("ENVIADA")).toBe("En camino");
    expect(etiquetaEstadoEntrega("RECOGIDA")).toBe("Recogida");
  });
});


describe("estilos de la vista de entrega", () => {
  it("carga los estilos compartidos del repartidor y los espec?ficos de entrega", () => {
    expect(paginaSource).toContain('import "./repartidor.css"');
    expect(paginaSource).toContain('import "./entrega.css"');
  });
});
