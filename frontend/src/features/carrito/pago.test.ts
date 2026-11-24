import { describe, expect, it } from "vitest";
import { esperarPago } from "./pago";

const sinEspera = { intervaloMs: 0, dormir: async () => {} };

describe("esperarPago", () => {
  it("termina en cuanto la orden deja de estar CREADA", async () => {
    const estados = ["CREADA", "CREADA", "PAGADA"] as const;
    let llamadas = 0;
    const r = await esperarPago(async () => ({ estado: estados[llamadas++] }), { ...sinEspera, intentos: 10 });
    expect(r).toBe("pagada");
    expect(llamadas).toBe(3);
  });

  it("si la confirmación no llega, avisa que sigue pendiente sin marcarla pagada", async () => {
    let llamadas = 0;
    const r = await esperarPago(async () => (llamadas++, { estado: "CREADA" as const }), { ...sinEspera, intentos: 4 });
    expect(r).toBe("pendiente");
    expect(llamadas).toBe(4);
  });

  it("un fallo de red momentáneo no se toma como pago fallido", async () => {
    let llamadas = 0;
    const r = await esperarPago(async () => {
      if (llamadas++ === 0) throw new Error("sin red");
      return { estado: "PAGADA" as const };
    }, { ...sinEspera, intentos: 3 });
    expect(r).toBe("pagada");
  });
});
