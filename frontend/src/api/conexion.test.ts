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

describe("errores RFC 7807", () => {
  it("expone el detalle, el código y los errores por campo", async () => {
    const problema = {
      type: "https://…/ERRORES.md#validacion", title: "Error de validación en los datos de entrada", status: 400,
      detail: "Uno o más campos del payload no cumplen con las reglas establecidas.", instance: "/auth/registro",
      codigo: "VALIDACION", invalid_params: [{ name: "credencial_unam", reason: "El número de cuenta UNAM tiene 9 dígitos" }],
    };
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response(JSON.stringify(problema), {
      status: 400, headers: { "Content-Type": "application/problem+json" },
    }))));
    await expect(api("/auth/registro", { method: "POST", body: {} })).rejects.toMatchObject({
      status: 400,
      codigo: "VALIDACION",
      message: problema.detail,
      campos: { credencial_unam: "El número de cuenta UNAM tiene 9 dígitos" },
    });
  });
});
