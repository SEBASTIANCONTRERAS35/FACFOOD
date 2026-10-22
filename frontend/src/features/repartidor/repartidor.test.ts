import { describe, expect, it } from "vitest";
import { textoDistancia, textoEstadoEntrega } from "./repartidor";

describe("presentación de entregas disponibles", () => {
  it("describe ambos estados elegibles", () => {
    expect(textoEstadoEntrega("PAGADA")).toBe("Pagado");
    expect(textoEstadoEntrega("EN_PREPARACION")).toBe("En preparación");
  });
  it("muestra la distancia que entrega el backend", () => {
    expect(textoDistancia("0.60")).toBe("0.60 km");
  });
});
