import { describe, expect, it } from "vitest";
import type { OrdenResumen } from "./pedidos";
import { agrupar, textoEstado } from "./pedidos";

const orden = (id: number, estado: OrdenResumen["estado"]): OrdenResumen => ({
  id, estado, punto_venta: { id: 1, nombre: "Tacos Don Memo" }, metodo_entrega: "pickup", piezas: 1, total: "18.00", creada_en: null,
});

describe("mis pedidos", () => {
  it("nombra el estado según el método de entrega", () => {
    expect(textoEstado("ENVIADA", "pickup")).toBe("Listo para recoger");
    expect(textoEstado("ENVIADA", "estudiante")).toBe("En camino");
    expect(textoEstado("EN_PREPARACION", "pickup")).toBe("En preparación");
  });

  it("separa los pedidos en curso de los entregados, sin cambiar el orden", () => {
    const { enCurso, anteriores } = agrupar([orden(5, "PAGADA"), orden(4, "ENTREGADA"), orden(3, "ENVIADA")]);
    expect(enCurso.map((o) => o.id)).toEqual([5, 3]);
    expect(anteriores.map((o) => o.id)).toEqual([4]);
  });
});
