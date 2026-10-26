import { afterEach, describe, expect, it, vi } from "vitest";
import { esIOS, estadoInstalacion, instalar } from "./instalacion";

const IPHONE = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1";
const ANDROID = "Mozilla/5.0 (Linux; Android 15) AppleWebKit/537.36 Chrome/131.0 Mobile Safari/537.36";

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("instalación de la PWA", () => {
  it("reconoce el iPhone para mostrar los pasos de Safari", () => {
    expect(esIOS(IPHONE)).toBe(true);
    expect(esIOS(ANDROID)).toBe(false);
    expect(estadoInstalacion(IPHONE)).toBe("ios");
  });

  it("ofrece instalar cuando el navegador dispara beforeinstallprompt", async () => {
    expect(estadoInstalacion(ANDROID)).toBe("no-disponible");
    const prompt = vi.fn(() => Promise.resolve());
    const evento = Object.assign(new Event("beforeinstallprompt", { cancelable: true }), {
      prompt,
      userChoice: Promise.resolve({ outcome: "accepted" as const }),
    });
    window.dispatchEvent(evento);
    expect(evento.defaultPrevented).toBe(true);
    expect(estadoInstalacion(ANDROID)).toBe("disponible");
    expect(await instalar()).toBe(true);
    expect(prompt).toHaveBeenCalledOnce();
    expect(estadoInstalacion(ANDROID)).toBe("no-disponible");
  });

  it("ya instalada (pantalla completa) no ofrece nada", () => {
    vi.stubGlobal("matchMedia", () => ({ matches: true }));
    expect(estadoInstalacion(IPHONE)).toBe("instalada");
  });
});
