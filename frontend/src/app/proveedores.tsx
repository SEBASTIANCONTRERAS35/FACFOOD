// Contextos globales (sesión, carrito). Dueño: Sebastián.
import type { ReactNode } from "react";
import { ProveedorCarrito } from "../features/carrito/carrito";
import { ProveedorSesion } from "../features/cuenta/sesion";

export function Proveedores({ children }: { children: ReactNode }) {
  return (
    <ProveedorSesion>
      <ProveedorCarrito>{children}</ProveedorCarrito>
    </ProveedorSesion>
  );
}
