import { describe, expect, it } from "vitest";
import type { Cupon, Lealtad } from "./cupones";
import { condiciones, progreso } from "./cupones";

const lealtad = (pedidos: number, siguiente: Lealtad["siguiente"]): Lealtad => ({
  nivel: "plata", descuento_pct: 5, pedidos_completados: pedidos, siguiente,
});

describe("cupones", () => {
  it("calcula el avance hacia el siguiente nivel", () => {
    expect(progreso(lealtad(3, { nivel: "oro", pedidos: 10, faltan: 7, descuento_pct: 10 }))).toBeCloseTo(0.3);
    expect(progreso(lealtad(12, null))).toBe(1);
  });

  it("describe las condiciones del cupón en español", () => {
    const bienvenida: Cupon = {
      codigo: "BIENVENIDA15", porcentaje: 15, pedido_minimo: "0.00", tope_descuento: "30.00",
      vigente_hasta: "2027-12-31", solo_primer_pedido: true, uno_por_usuario: true, estado: "disponible",
    };
    const texto = condiciones(bienvenida).join(" · ");
    expect(texto).toContain("Hasta $30.00 de descuento");
    expect(texto).toContain("Solo tu primer pedido");
    expect(texto).toContain("31");
    expect(texto).not.toContain("Pedido mínimo");
  });
});
