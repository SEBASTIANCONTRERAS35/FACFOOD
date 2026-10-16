import { describe, expect, it } from "vitest";
import { aCentavos, desdeCentavos, pesos } from "./dinero";

describe("dinero", () => {
  it("convierte texto a centavos sin errores de punto flotante", () => {
    expect(aCentavos("18.00") * 2 + aCentavos("30.00")).toBe(6600);
    expect(aCentavos("0.10") + aCentavos("0.20")).toBe(30);
    expect(aCentavos("9.9")).toBe(990);
  });

  it("vuelve a texto con dos decimales", () => {
    expect(desdeCentavos(6508)).toBe("65.08");
    expect(desdeCentavos(5)).toBe("0.05");
  });

  it("muestra pesos con separador de miles y signo menos", () => {
    expect(pesos("1240.00")).toBe("$1,240.00");
    expect(pesos("-9.90")).toBe("−$9.90");
  });
});
