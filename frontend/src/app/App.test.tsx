// Prueba de humo: la app arranca con el enrutador real y pinta las vistas públicas.
import { act } from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let contenedor: HTMLDivElement;

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn(() => Promise.reject(new Error("sin red en la prueba"))));
  contenedor = document.createElement("div");
  document.body.appendChild(contenedor);
});

afterEach(() => {
  vi.unstubAllGlobals();
  contenedor.remove();
  localStorage.clear();
});

async function montar(ruta: string) {
  const raiz = createRoot(contenedor);
  await act(async () => {
    raiz.render(
      <MemoryRouter initialEntries={[ruta]}>
        <App />
      </MemoryRouter>,
    );
  });
  return raiz;
}

describe("App", () => {
  it("muestra el registro con el consentimiento LFPDPPP", async () => {
    const raiz = await montar("/registro");
    expect(contenedor.textContent).toContain("Crea tu cuenta");
    expect(contenedor.textContent).toContain("LFPDPPP");
    act(() => raiz.unmount());
  });

  it("muestra el inicio de sesión", async () => {
    const raiz = await montar("/login");
    expect(contenedor.textContent).toContain("Inicia sesión");
    act(() => raiz.unmount());
  });

  it("una ruta que no existe muestra la página 404", async () => {
    const raiz = await montar("/no-existe");
    expect(contenedor.textContent).toContain("Esta página no existe");
    act(() => raiz.unmount());
  });

  it("el carrito pide iniciar sesión", async () => {
    const raiz = await montar("/carrito");
    expect(contenedor.textContent).toContain("Inicia sesión");
    act(() => raiz.unmount());
  });
});
