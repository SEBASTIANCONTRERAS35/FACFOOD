import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "./client";
import { hayConexion, suscribirConexion } from "./conexion";

function simularConexion(enLinea: boolean) {
  vi.spyOn(navigator, "onLine", "get").mockReturnValue(enLinea);
  window.dispatchEvent(new Event(enLinea ? "online" : "offline"));
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("conexión", () => {
  it("avisa cuando se pierde y cuando vuelve la conexión", () => {
    const aviso = vi.fn();
    const cancelar = suscribirConexion(aviso);
    simularConexion(false);
    expect(hayConexion()).toBe(false);
    simularConexion(true);
    expect(hayConexion()).toBe(true);
    expect(aviso).toHaveBeenCalledTimes(2);
    cancelar();
    simularConexion(false);
    expect(aviso).toHaveBeenCalledTimes(2);
  });

  it("sin conexión, la API responde con un mensaje claro", async () => {
    vi.spyOn(navigator, "onLine", "get").mockReturnValue(false);
    vi.stubGlobal("fetch", vi.fn(() => Promise.reject(new TypeError("Failed to fetch"))));
    await expect(api("/ordenes", { method: "POST", body: {} })).rejects.toMatchObject({
      status: 0,
      message: "Sin conexión. Revisa tu internet e intenta de nuevo.",
    });
  });
});
